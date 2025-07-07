"""
Baseline tests for Video2Doc refactoring using TDD approach.

These tests establish the current functionality before modularization.
Each test follows the Red-Green-Refactor cycle.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_video2doc_agent_can_be_initialized():
    """
    Red Phase: This test should fail initially.
    
    Tests that Video2DocAgent can be instantiated without errors.
    This is our baseline to ensure the agent class exists and can be imported.
    """
    from video2doc_agent import Video2DocAgent
    
    # Attempt to create an instance
    agent = Video2DocAgent()
    
    # Basic assertion that the agent was created
    assert agent is not None
    assert isinstance(agent, Video2DocAgent)

def test_youtube_url_detection_returns_boolean():
    """
    Red Phase: Test that is_youtube_url function returns boolean values.
    
    Tests basic YouTube URL detection functionality as a boolean function.
    This ensures the function interface remains stable during refactoring.
    """
    from utils.youtube import is_youtube_url
    
    # Test with a simple YouTube URL
    result = is_youtube_url("https://youtube.com/watch?v=test")
    assert isinstance(result, bool)
    
    # Test with non-URL string  
    result2 = is_youtube_url("not_a_url")
    assert isinstance(result2, bool)
    
    # Basic functionality test (should return True for valid YouTube URL)
    assert is_youtube_url("https://youtube.com/watch?v=test") == True

def test_workflow_creates_output_directory():
    """
    Red/Green Phase: Test that Video2DocWorkflow creates output directory.
    
    Tests that the workflow class properly initializes and creates its output directory.
    This ensures directory management functionality remains stable during refactoring.
    """
    import tempfile
    import shutil
    from core.workflow import Video2DocWorkflow
    from pathlib import Path
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "test_output")
        
        # Create workflow instance
        workflow = Video2DocWorkflow(output_dir=output_path)
        
        # Verify output directory was created
        assert os.path.exists(output_path)
        assert os.path.isdir(output_path)
        assert workflow.output_dir == Path(output_path)


if __name__ == "__main__":
    try:
        test_video2doc_agent_can_be_initialized()
        print("✅ test_video2doc_agent_can_be_initialized PASSED")
        
        test_youtube_url_detection_returns_boolean()
        print("✅ test_youtube_url_detection_returns_boolean PASSED")
        
        test_workflow_creates_output_directory()
        print("✅ test_workflow_creates_output_directory PASSED")
        
        print("🎉 모든 기준선 테스트 통과!")
        
    except Exception as e:
        print(f"❌ 기준선 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
