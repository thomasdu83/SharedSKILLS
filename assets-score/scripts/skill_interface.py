"""
Macro Strategy Research Skill Interface.

This module provides the interface for the AI Agent to interact with the Macro Strategy Research system.
It exposes tools for:
1. Preparing context (PDF extraction & text refinement)
2. Archiving results (Saving scores to Excel/DB)

Author: QuantSystem
Date: 2026-02-04
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# --- Path Configuration ---
# 1. Project Root (QuantSystem)
# Current: .trae/skills/assets-score/scripts/skill_interface.py
# Root is 5 levels up: scripts -> assets-score -> skills -> .trae -> QuantSystem
try:
    project_root = str(Path(__file__).parents[4])
except IndexError:
    # Fallback if path structure is unexpected
    project_root = str(Path(__file__).parent.parent.parent.parent.parent)

if project_root not in sys.path:
    sys.path.append(project_root)

# 2. Original Logic Path (for main.py and core modules)
logic_path = os.path.join(
    project_root, 
    "asset_allocation", "strategy_research", "宏观策略", "基于外部报告的宏观评分"
)
if logic_path not in sys.path:
    sys.path.append(logic_path)

# Import logic modules
try:
    from asset_allocation.strategy_research.宏观策略.基于外部报告的宏观评分.main import MacroReportAnalyzer
    from asset_allocation.strategy_research.宏观策略.基于外部报告的宏观评分.core.calculate_save import AssetScoreCalculator
except ImportError as e:
    logger.error(f"Failed to import core modules from {logic_path}: {e}")
    raise


def prepare_macro_context(pdf_folder_path: str = None, date_str: str = None) -> Dict[str, Any]:
    """
    Prepare the context for macro strategy analysis.
    
    1. Extracts and refines text from PDF reports in the given folder.
    2. Loads scoring prompts from the local filesystem.
    
    Args:
        pdf_folder_path: Path to the folder containing PDF reports. 
                         If provided, overrides date_str logic.
        date_str: Date string (YYYY-MM-DD) to specify which day's reports to analyze.
                  If None, defaults to today's date or falls back to latest available.
    
    Returns:
        Dict containing:
        - summary_text: The refined summary of all reports.
        - prompts: A dictionary of scoring prompts (conservative, aggressive, dialectical).
        - status: "success" or "error".
        - message: Error message if any.
    """
    try:
        # Default path logic if not provided
        if not pdf_folder_path:
            from datetime import datetime
            try:
                from main_config import MAIN_DRIVE
            except ImportError:
                # Fallback if main_config is not found (though it should be in project_root)
                MAIN_DRIVE = "f:" # Assumption based on env
            
            base_reports_path = f"{MAIN_DRIVE}\\Thomas\\Note\\MyNotes\\00_资产配置\\00_观点跟踪\\外部研究报告跟踪"
            
            if date_str:
                # 1. Try to use the specified date
                target_path = os.path.join(base_reports_path, date_str)
                if os.path.exists(target_path):
                    pdf_folder_path = target_path
                    logger.info(f"Using specified date folder: {pdf_folder_path}")
                else:
                    return {
                        "status": "error",
                        "message": f"Reports folder for specified date {date_str} not found at {target_path}"
                    }
            else:
                # 2. Fallback logic: Today -> Latest
                current_date_str = datetime.now().strftime("%Y-%m-%d")
                today_path = os.path.join(base_reports_path, current_date_str)
                
                if os.path.exists(today_path):
                    pdf_folder_path = today_path
                else:
                    logger.info(f"Today's folder {today_path} not found. Searching for latest...")
                    # Find latest date folder
                    try:
                        if os.path.exists(base_reports_path):
                            dirs = [d for d in os.listdir(base_reports_path) if os.path.isdir(os.path.join(base_reports_path, d))]
                            date_dirs = []
                            for d in dirs:
                                try:
                                    datetime.strptime(d, "%Y-%m-%d")
                                    date_dirs.append(d)
                                except ValueError:
                                    continue
                            
                            if date_dirs:
                                date_dirs.sort(reverse=True)
                                pdf_folder_path = os.path.join(base_reports_path, date_dirs[0])
                                logger.info(f"Using latest available folder: {pdf_folder_path}")
                            else:
                                 # No date folders, fall back to today to let it try or fail
                                pdf_folder_path = today_path
                        else:
                            pdf_folder_path = today_path
                    except Exception as e:
                        logger.warning(f"Error searching for latest folder: {e}")
                        pdf_folder_path = today_path

            
        logger.info(f"Preparing macro context from: {pdf_folder_path}")
        
        # Initialize Analyzer
        analyzer = MacroReportAnalyzer()
        
        # Step 1: Extract and Refine Reports
        # Check if summary already exists to save time
        summary_filename = f"宏观策略报告汇总{os.path.basename(pdf_folder_path)}.md"
        summary_path = os.path.join(analyzer.refined_output_dir, summary_filename)
        
        if os.path.exists(summary_path):
            logger.info(f"Found existing summary at {summary_path}, loading directly.")
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_text = f.read()
        else:
            logger.info("Extracting and refining reports (this may take a while)...")
            summary_text = analyzer.extract_and_refine_reports(
                reports_path=pdf_folder_path,
                save_summary=True,
                summary_filename=summary_filename
            )
            
        # Step 2: Load Prompts
        # Prompts are located in the original logic directory
        prompts_dir = os.path.join(logic_path, "prompts")
        prompts = {}
        
        prompt_files = {
            "conservative": "conservative_scoring_prompt.md",
            "aggressive": "aggressive_scoring_prompt.md",
            "dialectical": "dialectical_scoring_prompt.md"
        }
        
        for style, filename in prompt_files.items():
            path = os.path.join(prompts_dir, filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    prompts[style] = f.read()
            else:
                logger.warning(f"Prompt file not found: {path}")
                prompts[style] = "Prompt file missing."

        return {
            "status": "success",
            "summary_text": summary_text,
            "prompts": prompts,
            "source_path": pdf_folder_path
        }

    except Exception as e:
        logger.error(f"Error in prepare_macro_context: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


def archive_macro_results(
    scoring_results: Dict[str, Any], 
    date_str: str = None
) -> Dict[str, Any]:
    """
    Archive the macro strategy scoring results.
    
    1. Saves the JSON results to the db folder.
    2. Runs the calculator to aggregate scores and save to Excel/SQLite.
    
    Args:
        scoring_results: Dictionary containing the scoring results for each style.
                         Expected keys: 'conservative', 'aggressive', 'dialectical'.
                         Each value should be the JSON object (dict) of the score.
        date_str: Date string (YYYY-MM-DD). If None, uses today.
        
    Returns:
        Dict containing status and saved paths.
    """
    try:
        if date_str is None:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        logger.info(f"Archiving macro results for date: {date_str}")
        
        # Validate inputs
        required_styles = ["conservative", "aggressive", "dialectical"]
        formatted_results = []
        
        for style in required_styles:
            if style not in scoring_results:
                raise ValueError(f"Missing scoring result for style: {style}")
            
            # Wrap in the format expected by ResultSaver: {"score": ..., "rationale": ...}
            # Assuming the Agent returns just the score dict or a dict with rationale
            style_data = scoring_results[style]
            
            # Normalize data structure
            if "score" not in style_data:
                # If the agent returned just the score dict, wrap it
                formatted_results.append({
                    "score": style_data,
                    "rationale": style_data.get("rationale", "Generated by Trae Agent")
                })
            else:
                formatted_results.append(style_data)

        # Initialize Analyzer for saving tools
        analyzer = MacroReportAnalyzer()
        
        # Step 1: Save JSON/Markdown results
        analyzer.save_results(formatted_results)
        logger.info("Intermediate JSON/Markdown files saved.")
        
        # Step 2: Calculate and Save to DB/Excel
        # Use logic_path for workpath since AssetScoreCalculator expects db/config relative to it
        workpath = logic_path
        calculator = AssetScoreCalculator(workpath)
        
        final_df = calculator.run(
            date_str=date_str,
            save_to_shared=True
        )
        
        return {
            "status": "success",
            "message": "Results archived successfully to Excel and Database.",
            "output_dir": os.path.join(workpath, "db"),
            "row_count": len(final_df)
        }

    except Exception as e:
        logger.error(f"Error in archive_macro_results: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
