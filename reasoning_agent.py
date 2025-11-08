#!/usr/bin/env python3
"""
AI-Powered Reasoning Agent for Invoice Validation and Duplication Analysis

This module uses LangChain and LangGraph to provide intelligent, detailed explanations
for arithmetic validation results and duplication analysis outcomes. The AI agent
analyzes validation failures, duplication patterns, and provides actionable insights.

Features:
1. LangGraph workflow for structured reasoning
2. LangChain LLM integration for natural language explanations
3. Context-aware analysis of validation failures
4. Intelligent duplication pattern recognition
5. Actionable recommendations for business users
6. Multi-step reasoning with evidence synthesis
"""

import json
import re
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

@dataclass
class ReasoningContext:
    """Context data for reasoning analysis"""
    invoice_data: Dict[str, Any]
    validation_results: Optional[Dict[str, Any]] = None
    duplication_results: Optional[Dict[str, Any]] = None
    analysis_type: str = "validation"  # "validation", "duplication", or "both"

class ReasoningState(TypedDict):
    """State for the reasoning workflow"""
    context: ReasoningContext
    validation_reasoning: str
    duplication_reasoning: str
    business_impact: str
    recommendations: List[str]
    confidence_score: float
    final_explanation: str

class AIReasoningAgent:
    """AI-powered reasoning agent using LangChain and LangGraph"""
    
    def __init__(self, llm_model: str = "models/gemini-2.5-flash"):
        """Initialize the reasoning agent"""
        self.llm = None
        self.api_available = False
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=llm_model,
                temperature=0.3,  # Lower temperature for more consistent reasoning
                max_tokens=2000
            )
            # Test if the API works
            self.llm.invoke("test")
            self.api_available = True
            print(f"🧠 AI Reasoning Agent initialized with {llm_model}")
        except Exception as e:
            print(f"⚠️  AI Reasoning initialization failed: {str(e)[:100]}...")
            print("AI reasoning will use fallback mode.")
            self.api_available = False
        
        # Create LangGraph workflow
        self.workflow = self._create_reasoning_workflow()
        
        print(f"🧠 AI Reasoning Agent initialized with {llm_model}")
    
    def _create_reasoning_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for reasoning"""
        workflow = StateGraph(ReasoningState)
        
        # Add nodes
        workflow.add_node("analyze_validation", self._analyze_validation_node)
        workflow.add_node("analyze_duplication", self._analyze_duplication_node)
        workflow.add_node("assess_business_impact", self._assess_business_impact_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("synthesize_explanation", self._synthesize_explanation_node)
        
        # Define the workflow
        workflow.set_entry_point("analyze_validation")
        workflow.add_edge("analyze_validation", "analyze_duplication")
        workflow.add_edge("analyze_duplication", "assess_business_impact")
        workflow.add_edge("assess_business_impact", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "synthesize_explanation")
        workflow.add_edge("synthesize_explanation", END)
        
        return workflow.compile()
    
    async def _analyze_validation_node(self, state: ReasoningState) -> ReasoningState:
        """Analyze arithmetic validation results with AI reasoning"""
        context = state["context"]
        
        if not context.validation_results:
            state["validation_reasoning"] = "No validation data available for analysis."
            return state
        
        # If API is not available, use fallback reasoning
        if not self.api_available:
            state["validation_reasoning"] = self._fallback_validation_reasoning(context.validation_results)
            return state
        
        validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial analyst specializing in invoice validation.
            Analyze the arithmetic validation results and provide clear, detailed explanations.
            Focus on:
            1. What specific calculations failed and why
            2. Root causes of validation failures
            3. Data quality issues that may have contributed
            4. Financial accuracy implications
            
            Be specific, accurate, and business-focused in your explanations."""),
            ("human", """Analyze these invoice validation results:
            
            Invoice Details:
            {invoice_data}
            
            Validation Results:
            {validation_results}
            
            Provide a detailed explanation of the validation outcome, focusing on:
            - Why specific tests failed
            - Potential data extraction or calculation errors
            - Financial accuracy concerns
            - Impact on invoice processing""")
        ])
        
        try:
            messages = validation_prompt.format_messages(
                invoice_data=json.dumps(context.invoice_data, indent=2),
                validation_results=json.dumps(context.validation_results, indent=2)
            )
            
            response = await self.llm.ainvoke(messages)
            state["validation_reasoning"] = response.content
            
        except Exception as e:
            state["validation_reasoning"] = f"AI analysis failed: {str(e)}. Using fallback reasoning."
            state["validation_reasoning"] += self._fallback_validation_reasoning(context.validation_results)
        
        return state
    
    async def _analyze_duplication_node(self, state: ReasoningState) -> ReasoningState:
        """Analyze duplication detection results with AI reasoning"""
        context = state["context"]
        
        if not context.duplication_results:
            state["duplication_reasoning"] = "No duplication analysis data available."
            return state
        
        # If API is not available, use fallback reasoning
        if not self.api_available:
            state["duplication_reasoning"] = self._fallback_duplication_reasoning(context.duplication_results)
            return state
        
        duplication_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in financial fraud detection and duplicate invoice analysis.
            Analyze the duplication detection results and provide clear explanations.
            Focus on:
            1. Patterns that indicate potential duplicates
            2. Confidence levels and their significance
            3. Business risk assessment
            4. Recommended actions based on evidence
            
            Be thorough in explaining the logic behind duplication detection."""),
            ("human", """Analyze these invoice duplication results:
            
            Invoice Details:
            {invoice_data}
            
            Duplication Analysis:
            {duplication_results}
            
            Provide detailed reasoning covering:
            - Why this invoice is/isn't considered a duplicate
            - Evidence supporting the conclusion
            - Risk level and business implications
            - Recommended verification steps""")
        ])
        
        try:
            messages = duplication_prompt.format_messages(
                invoice_data=json.dumps(context.invoice_data, indent=2),
                duplication_results=json.dumps(context.duplication_results, indent=2)
            )
            
            response = await self.llm.ainvoke(messages)
            state["duplication_reasoning"] = response.content
            
        except Exception as e:
            state["duplication_reasoning"] = f"AI analysis failed: {str(e)}. Using fallback reasoning."
            state["duplication_reasoning"] += self._fallback_duplication_reasoning(context.duplication_results)
        
        return state
    
    async def _assess_business_impact_node(self, state: ReasoningState) -> ReasoningState:
        """Assess overall business impact"""
        context = state["context"]
        
        # If API is not available, use fallback assessment
        if not self.api_available:
            state["business_impact"] = self._fallback_business_impact(context)
            return state
        
        impact_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a business analyst specializing in financial process optimization.
            Assess the business impact of validation and duplication analysis results.
            Consider financial, operational, and compliance implications."""),
            ("human", """Based on the validation and duplication analysis:
            
            Validation Reasoning: {validation_reasoning}
            Duplication Reasoning: {duplication_reasoning}
            Invoice Amount: {invoice_amount}
            
            Assess the business impact in terms of:
            - Financial risk level
            - Process efficiency impact
            - Compliance considerations
            - Operational recommendations""")
        ])
        
        try:
            invoice_amount = context.invoice_data.get('total_value', 'Unknown')
            
            messages = impact_prompt.format_messages(
                validation_reasoning=state["validation_reasoning"],
                duplication_reasoning=state["duplication_reasoning"],
                invoice_amount=invoice_amount
            )
            
            response = await self.llm.ainvoke(messages)
            state["business_impact"] = response.content
            
        except Exception as e:
            state["business_impact"] = f"Impact assessment unavailable: {str(e)}"
        
        return state
    
    async def _generate_recommendations_node(self, state: ReasoningState) -> ReasoningState:
        """Generate actionable recommendations"""
        context = state["context"]
        
        # Extract key issues for recommendation generation
        validation_failed = context.validation_results and not context.validation_results.get('overall_passed', True)
        has_duplicates = context.duplication_results and context.duplication_results.get('is_duplicate', False)
        
        recommendations = []
        
        if validation_failed:
            recommendations.extend([
                "Review invoice calculations for mathematical accuracy",
                "Verify data extraction quality from source documents",
                "Check for manual entry errors in invoice processing"
            ])
        
        if has_duplicates:
            recommendations.extend([
                "Investigate potential duplicate submission",
                "Cross-reference with payment records",
                "Implement additional duplicate prevention controls"
            ])
        
        if not validation_failed and not has_duplicates:
            recommendations.extend([
                "Proceed with standard invoice processing",
                "Archive for compliance records",
                "Update vendor processing metrics"
            ])
        
        # If API is available, try to enhance recommendations
        if self.api_available:
            try:
                # Add AI-enhanced recommendations
                rec_prompt = ChatPromptTemplate.from_messages([
                    ("system", "Generate 3-5 specific, actionable recommendations based on the analysis results."),
                    ("human", """Based on this analysis:
                    Validation: {validation_reasoning}
                    Duplication: {duplication_reasoning}
                    Business Impact: {business_impact}
                    
                    Generate specific recommendations for next steps.""")
                ])
                
                messages = rec_prompt.format_messages(
                    validation_reasoning=state["validation_reasoning"],
                    duplication_reasoning=state["duplication_reasoning"],
                    business_impact=state["business_impact"]
                )
                
                response = await self.llm.ainvoke(messages)
                ai_recommendations = response.content.split('\n')
                ai_recommendations = [rec.strip('- ').strip() for rec in ai_recommendations if rec.strip()]
                
                recommendations.extend(ai_recommendations[:3])  # Add top 3 AI recommendations
                
            except Exception as e:
                recommendations.append(f"AI recommendation generation failed: {str(e)}")
        
        state["recommendations"] = recommendations[:5]  # Limit to 5 recommendations
        return state
    
    async def _synthesize_explanation_node(self, state: ReasoningState) -> ReasoningState:
        """Synthesize final explanation"""
        synthesis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Synthesize all analysis into a clear, executive summary.
            Create a concise explanation that business users can easily understand.
            Include confidence assessment and key action items."""),
            ("human", """Synthesize this analysis into a clear executive summary:
            
            Validation: {validation_reasoning}
            Duplication: {duplication_reasoning}
            Business Impact: {business_impact}
            Recommendations: {recommendations}
            
            Create a 2-3 sentence summary explaining the overall assessment and key actions needed.""")
        ])
        
        try:
            recommendations_text = "; ".join(state["recommendations"])
            
            messages = synthesis_prompt.format_messages(
                validation_reasoning=state["validation_reasoning"],
                duplication_reasoning=state["duplication_reasoning"],
                business_impact=state["business_impact"],
                recommendations=recommendations_text
            )
            
            response = await self.llm.ainvoke(messages)
            state["final_explanation"] = response.content
            
            # Calculate confidence score based on analysis outcomes
            state["confidence_score"] = self._calculate_confidence_score(state)
            
        except Exception as e:
            state["final_explanation"] = "Analysis synthesis unavailable due to AI processing error."
            state["confidence_score"] = 0.5
        
        return state
    
    def _calculate_confidence_score(self, state: ReasoningState) -> float:
        """Calculate overall confidence score"""
        context = state["context"]
        
        confidence = 1.0
        
        # Reduce confidence for validation failures
        if context.validation_results and not context.validation_results.get('overall_passed', True):
            failed_tests = context.validation_results.get('tests_failed', 0)
            total_tests = context.validation_results.get('tests_run', 1)
            confidence *= (1 - (failed_tests / total_tests) * 0.3)  # Max 30% reduction
        
        # Reduce confidence for duplication concerns
        if context.duplication_results and context.duplication_results.get('is_duplicate', False):
            dup_confidence = context.duplication_results.get('confidence_score', 0)
            confidence *= (1 - dup_confidence * 0.5)  # Up to 50% reduction for high dup confidence
        
        return max(0.1, min(1.0, confidence))
    
    def _fallback_validation_reasoning(self, validation_results: Dict) -> str:
        """Fallback reasoning for validation when AI is unavailable"""
        if not validation_results:
            return " No validation data to analyze."
        
        failed_tests = validation_results.get('tests_failed', 0)
        total_tests = validation_results.get('tests_run', 0)
        
        if failed_tests == 0:
            return " All arithmetic validations passed successfully, indicating mathematical consistency."
        else:
            return f" {failed_tests} out of {total_tests} validation tests failed, indicating potential calculation errors or data extraction issues."
    
    def _fallback_duplication_reasoning(self, duplication_results: Dict) -> str:
        """Fallback reasoning for duplication when AI is unavailable"""
        if not duplication_results:
            return " No duplication analysis data available."
        
        if duplication_results.get('is_duplicate', False):
            confidence = duplication_results.get('confidence_score', 0)
            return f" Potential duplicate detected with {confidence:.1%} confidence based on pattern matching."
        else:
            return " No significant duplicate patterns detected across comparison criteria."
    
    def _fallback_business_impact(self, context: ReasoningContext) -> str:
        """Fallback business impact assessment"""
        validation_failed = context.validation_results and not context.validation_results.get('overall_passed', True)
        has_duplicates = context.duplication_results and context.duplication_results.get('is_duplicate', False)
        amount = context.invoice_data.get('total_value', 0)
        
        impact = []
        
        if validation_failed:
            impact.append("Financial accuracy concerns due to validation failures")
            if amount > 100000:
                impact.append("High-value transaction requires careful review")
        
        if has_duplicates:
            impact.append("Potential duplicate payment risk")
            impact.append("Process efficiency impact due to duplicate detection")
        
        if not validation_failed and not has_duplicates:
            impact.append("Low risk transaction - standard processing recommended")
            impact.append("Good data quality and no duplicate concerns")
        
        return ". ".join(impact) + "."
    
    async def analyze(self, context: ReasoningContext) -> Dict[str, Any]:
        """Perform comprehensive AI-powered reasoning analysis"""
        print("🧠 Running AI-powered reasoning analysis...")
        
        initial_state = ReasoningState(
            context=context,
            validation_reasoning="",
            duplication_reasoning="",
            business_impact="",
            recommendations=[],
            confidence_score=0.0,
            final_explanation=""
        )
        
        try:
            # Run the LangGraph workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            return {
                "validation_reasoning": final_state["validation_reasoning"],
                "duplication_reasoning": final_state["duplication_reasoning"],
                "business_impact": final_state["business_impact"],
                "recommendations": final_state["recommendations"],
                "confidence_score": final_state["confidence_score"],
                "final_explanation": final_state["final_explanation"],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"⚠️  AI reasoning analysis failed: {str(e)}")
            # Return fallback analysis
            return self._create_fallback_analysis(context)
    
    def _create_fallback_analysis(self, context: ReasoningContext) -> Dict[str, Any]:
        """Create fallback analysis when AI processing fails"""
        return {
            "validation_reasoning": self._fallback_validation_reasoning(context.validation_results),
            "duplication_reasoning": self._fallback_duplication_reasoning(context.duplication_results),
            "business_impact": "Unable to assess business impact due to AI processing limitations.",
            "recommendations": ["Review results manually", "Verify data accuracy", "Consult with finance team"],
            "confidence_score": 0.5,
            "final_explanation": "Automated AI analysis unavailable. Manual review recommended.",
            "analysis_timestamp": datetime.now().isoformat(),
            "fallback_mode": True
        }
    
    def print_detailed_reasoning(self, analysis_result: Dict[str, Any], invoice_data: Dict[str, Any]):
        """Print formatted detailed reasoning results"""
        print(f"\n🧠 AI-POWERED DETAILED REASONING")
        print("=" * 60)
        
        invoice_num = invoice_data.get('invoice_num', 'Unknown')
        supplier = invoice_data.get('supplier_name', 'Unknown')
        amount = invoice_data.get('total_value', 'Unknown')
        
        print(f"📄 Invoice: {invoice_num}")
        print(f"🏢 Supplier: {supplier}")
        print(f"💰 Amount: ₹{amount}")
        print(f"🎯 AI Confidence: {analysis_result['confidence_score']:.1%}")
        
        print(f"\n🧮 VALIDATION REASONING:")
        print("-" * 40)
        print(analysis_result['validation_reasoning'])
        
        print(f"\n🔍 DUPLICATION REASONING:")
        print("-" * 40)
        print(analysis_result['duplication_reasoning'])
        
        print(f"\n📊 BUSINESS IMPACT ASSESSMENT:")
        print("-" * 40)
        print(analysis_result['business_impact'])
        
        print(f"\n💡 AI RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(analysis_result['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n🎯 EXECUTIVE SUMMARY:")
        print("-" * 40)
        print(analysis_result['final_explanation'])
        
        if analysis_result.get('fallback_mode'):
            print("\n⚠️  Note: AI analysis unavailable, using fallback reasoning.")

async def main():
    """Test the AI reasoning agent"""
    print("🧠 AI REASONING AGENT TEST")
    print("=" * 50)
    
    # Sample data for testing
    invoice_data = {
        "invoice_id": 1,
        "invoice_num": "SBD/25-26/197",
        "supplier_name": "ISKO ENGINEERING PVT LTD",
        "total_value": 1208074.56,
        "taxable_value": 1023792.00,
        "total_tax": 184282.56
    }
    
    validation_results = {
        "tests_run": 4,
        "tests_passed": 3,
        "tests_failed": 1,
        "overall_passed": False,
        "failed_tests": [
            {"test_name": "Invoice Tax Sum", "error": "Sum of line item taxes(0) ≠ Invoice tax(184282.56)"}
        ]
    }
    
    duplication_results = {
        "is_duplicate": False,
        "confidence_score": 0.0,
        "duplicate_matches": [],
        "recommended_action": "APPROVE_AS_UNIQUE"
    }
    
    # Create reasoning context
    context = ReasoningContext(
        invoice_data=invoice_data,
        validation_results=validation_results,
        duplication_results=duplication_results,
        analysis_type="both"
    )
    
    # Run analysis
    agent = AIReasoningAgent()
    result = await agent.analyze(context)
    
    # Print results
    agent.print_detailed_reasoning(result, invoice_data)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())