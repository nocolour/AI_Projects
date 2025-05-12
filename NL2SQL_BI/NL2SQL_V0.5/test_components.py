#!/usr/bin/env python3
"""
Integration test script to validate all components are properly connected
"""

import os
import sys
import importlib
import traceback
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init()

def print_success(message):
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED}✘ {message}{Style.RESET_ALL}")

def print_header(message):
    print(f"\n{Fore.CYAN}=== {message} ==={Style.RESET_ALL}")

def test_module_imports():
    print_header("Testing Module Imports")
    modules_to_test = [
        "modules.database_manager", 
        "modules.ai_manager",
        "modules.visualization_manager",
        "modules.ui_manager",
        "modules.settings_manager",
        "modules.task_manager",
        "modules.visualization.manager",
        "modules.visualization.chart_recommender",
        "modules.visualization.chart_creators",
        "modules.visualization.data_processor",
        "modules.visualization.clipboard_utils",
        "modules.visualization.charts.ai_enhancer",
        "modules.visualization.charts.bar_charts",
        "modules.visualization.charts.line_charts",
        "modules.visualization.charts.scatter_charts",
        "modules.visualization.charts.pie_charts",
        "modules.visualization.charts.fallback_charts",
    ]
    
    success_count = 0
    warning_count = 0
    error_count = 0
    
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print_success(f"Imported {module_name}")
            success_count += 1
        except ModuleNotFoundError as e:
            print_error(f"Failed to import {module_name}: {e}")
            error_count += 1
        except Exception as e:
            print_warning(f"Import issue with {module_name}: {e}")
            warning_count += 1
    
    print(f"\nImport summary: {success_count} successful, {warning_count} warnings, {error_count} errors")
    return error_count == 0

def test_component_initialization():
    print_header("Testing Component Initialization")
    
    try:
        from modules.database_manager import DatabaseManager
        from modules.ai_manager import AIManager
        from modules.visualization_manager import VisualizationManager
        from modules.task_manager import TaskManager
        
        print("Initializing components...")
        db_manager = DatabaseManager()
        ai_manager = AIManager()
        vis_manager = VisualizationManager(ai_manager=ai_manager)
        task_manager = TaskManager()
        
        print_success("All components initialized successfully")
        return True
    except Exception as e:
        print_error(f"Component initialization failed: {e}")
        traceback.print_exc()
        return False

def main():
    print_header("NL2SQL Component Integration Test")
    
    # Run tests
    imports_ok = test_module_imports()
    init_ok = test_component_initialization()
    
    # Summary
    print_header("Test Summary")
    if imports_ok:
        print_success("All required modules can be imported")
    else:
        print_error("Some modules could not be imported")
        
    if init_ok:
        print_success("All components initialize correctly")
    else:
        print_error("Component initialization failed")
    
    if imports_ok and init_ok:
        print_success("All tests passed! The application should run properly.")
        return 0
    else:
        print_error("Some tests failed. Please fix the issues before running the application.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
