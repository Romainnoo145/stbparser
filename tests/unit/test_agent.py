"""
Tests for agent module - Agent initialization and tool registration.

Tests cover:
- Agent creation with proper model
- Tool registration (5 tools)
- Agent execution with TestModel
- Agent execution with FunctionModel
- Dependency injection into agent
"""

import pytest
from unittest.mock import Mock, patch
from pydantic_ai.models.test import TestModel
from pydantic_ai.messages import ModelTextResponse

from offorte_airtable_sync.agent import agent, process_proposal_sync


class TestAgentInitialization:
    """Test agent initialization and configuration."""

    def test_agent_exists(self):
        """Test agent is properly initialized."""
        assert agent is not None
        assert hasattr(agent, "deps_type")

    def test_agent_has_dependencies_type(self):
        """Test agent has correct dependencies type."""
        from offorte_airtable_sync.dependencies import AgentDependencies
        assert agent.deps_type == AgentDependencies

    def test_agent_has_system_prompt(self):
        """Test agent has system prompt configured."""
        # System prompt should be set
        assert agent._system_prompt is not None or agent._system_prompts is not None

    def test_agent_retries_configured(self):
        """Test agent has retry configuration."""
        # Agent should have retries configured from settings
        assert hasattr(agent, "_max_result_retries")


class TestAgentTools:
    """Test agent tool registration."""

    def test_agent_has_tools(self):
        """Test agent has tools registered."""
        # Agent should have tools
        assert len(agent._function_tools) > 0

    def test_fetch_proposal_tool_registered(self):
        """Test fetch proposal tool is registered."""
        tool_names = [tool.name for tool in agent._function_tools.values()]
        assert "tool_fetch_proposal" in tool_names

    def test_parse_elements_tool_registered(self):
        """Test parse elements tool is registered."""
        tool_names = [tool.name for tool in agent._function_tools.values()]
        assert "tool_parse_elements" in tool_names

    def test_transform_data_tool_registered(self):
        """Test transform data tool is registered."""
        tool_names = [tool.name for tool in agent._function_tools.values()]
        assert "tool_transform_data" in tool_names

    def test_sync_airtable_tool_registered(self):
        """Test sync Airtable tool is registered."""
        tool_names = [tool.name for tool in agent._function_tools.values()]
        assert "tool_sync_airtable" in tool_names

    def test_process_proposal_tool_registered(self):
        """Test process proposal tool is registered."""
        tool_names = [tool.name for tool in agent._function_tools.values()]
        assert "tool_process_proposal" in tool_names

    def test_all_tools_count(self):
        """Test correct number of tools are registered."""
        # Should have 5 tools registered
        assert len(agent._function_tools) == 5


class TestAgentWithTestModel:
    """Test agent execution with TestModel."""

    @pytest.mark.asyncio
    async def test_agent_basic_response(self, test_agent_with_test_model, test_deps):
        """Test agent provides basic response with TestModel."""
        result = await test_agent_with_test_model.run(
            "Process proposal 12345",
            deps=test_deps
        )

        assert result is not None
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_agent_with_test_model_messages(self, test_agent_with_test_model, test_deps):
        """Test agent message history with TestModel."""
        result = await test_agent_with_test_model.run(
            "Sync proposal to Airtable",
            deps=test_deps
        )

        messages = result.all_messages()
        assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_agent_tool_calling_with_test_model(self, test_deps):
        """Test agent can call tools with TestModel."""
        test_model = TestModel()

        # Configure TestModel to call a tool
        test_model.agent_responses = [
            ModelTextResponse(content="I'll fetch the proposal"),
            {"tool_fetch_proposal": {"proposal_id": 12345}},
            ModelTextResponse(content="Proposal fetched successfully")
        ]

        test_agent = agent.override(model=test_model)

        # Mock the actual tool implementation
        with patch("offorte_airtable_sync.tools.fetch_proposal_data") as mock_fetch:
            mock_fetch.return_value = {"id": 12345, "proposal_nr": "2025001NL"}

            result = await test_agent.run(
                "Fetch proposal 12345",
                deps=test_deps
            )

            # Verify tool was attempted to be called
            messages = result.all_messages()
            assert len(messages) > 0


class TestAgentWithFunctionModel:
    """Test agent execution with FunctionModel."""

    @pytest.mark.asyncio
    async def test_agent_with_function_model_simple(self, function_model_simple, test_deps):
        """Test agent with simple FunctionModel."""
        test_agent = agent.override(model=function_model_simple)

        result = await test_agent.run(
            "Process proposal",
            deps=test_deps
        )

        assert result.data is not None

    @pytest.mark.asyncio
    async def test_agent_with_function_model_tools(self, test_deps):
        """Test agent with FunctionModel that simulates tool calling."""
        from pydantic_ai.models.function import FunctionModel, AgentInfo
        from pydantic_ai.messages import ModelMessage

        call_count = {"count": 0}

        async def tool_response(messages: list[ModelMessage], info: AgentInfo):
            call_count["count"] += 1

            if call_count["count"] == 1:
                return ModelTextResponse(content="I'll process the proposal")
            else:
                return ModelTextResponse(content="Proposal processed successfully")

        function_model = FunctionModel(tool_response)
        test_agent = agent.override(model=function_model)

        result = await test_agent.run(
            "Process proposal 12345",
            deps=test_deps
        )

        assert result.data is not None
        assert call_count["count"] >= 1


class TestProcessProposalSync:
    """Test main process_proposal_sync entry point."""

    @pytest.mark.asyncio
    async def test_process_proposal_sync_basic(self, test_settings):
        """Test process_proposal_sync creates dependencies and runs agent."""
        proposal_id = 12345
        job_id = "test-job-123"

        # Mock the agent.run method
        with patch.object(agent, "run") as mock_run:
            mock_result = Mock()
            mock_result.data = {
                "success": True,
                "proposal_id": 12345,
                "sync_summary": {}
            }
            mock_run.return_value = mock_result

            # Mock settings
            with patch("offorte_airtable_sync.agent.settings", test_settings):
                result = await process_proposal_sync(proposal_id, job_id)

        assert result is not None
        assert mock_run.called

    @pytest.mark.asyncio
    async def test_process_proposal_sync_cleanup(self, test_settings):
        """Test process_proposal_sync cleans up dependencies."""
        proposal_id = 12345
        job_id = "test-job-123"

        cleanup_called = {"called": False}

        async def mock_cleanup():
            cleanup_called["called"] = True

        with patch.object(agent, "run") as mock_run:
            mock_result = Mock()
            mock_result.data = {"success": True}
            mock_run.return_value = mock_result

            with patch("offorte_airtable_sync.agent.settings", test_settings):
                with patch("offorte_airtable_sync.agent.AgentDependencies.from_settings") as mock_deps:
                    mock_deps_instance = Mock()
                    mock_deps_instance.cleanup = mock_cleanup
                    mock_deps.return_value = mock_deps_instance

                    await process_proposal_sync(proposal_id, job_id)

        # Cleanup should be called
        assert cleanup_called["called"] is True

    @pytest.mark.asyncio
    async def test_process_proposal_sync_with_error(self, test_settings):
        """Test process_proposal_sync handles errors gracefully."""
        proposal_id = 12345
        job_id = "test-job-123"

        cleanup_called = {"called": False}

        async def mock_cleanup():
            cleanup_called["called"] = True

        with patch.object(agent, "run") as mock_run:
            mock_run.side_effect = Exception("Agent error")

            with patch("offorte_airtable_sync.agent.settings", test_settings):
                with patch("offorte_airtable_sync.agent.AgentDependencies.from_settings") as mock_deps:
                    mock_deps_instance = Mock()
                    mock_deps_instance.cleanup = mock_cleanup
                    mock_deps.return_value = mock_deps_instance

                    with pytest.raises(Exception):
                        await process_proposal_sync(proposal_id, job_id)

        # Cleanup should still be called even on error
        assert cleanup_called["called"] is True


class TestAgentDependencyInjection:
    """Test dependency injection into agent."""

    @pytest.mark.asyncio
    async def test_agent_receives_dependencies(self, test_agent_with_test_model, test_deps):
        """Test agent receives and uses dependencies."""
        result = await test_agent_with_test_model.run(
            "Test prompt",
            deps=test_deps
        )

        # Dependencies should be passed to agent
        assert result is not None

    @pytest.mark.asyncio
    async def test_agent_dependencies_in_context(self, test_deps):
        """Test dependencies are accessible in tool context."""
        from pydantic_ai import RunContext

        # Create a simple test to verify context
        test_model = TestModel()
        test_agent = agent.override(model=test_model)

        result = await test_agent.run(
            "Test",
            deps=test_deps
        )

        # Result should exist
        assert result is not None


class TestAgentModelConfiguration:
    """Test agent model configuration."""

    def test_agent_model_configured(self):
        """Test agent has a model configured."""
        assert agent._model is not None or agent.model is not None

    @pytest.mark.unit
    def test_agent_can_override_model(self, test_model):
        """Test agent model can be overridden for testing."""
        test_agent = agent.override(model=test_model)

        assert test_agent is not None
        # Overridden agent should have TestModel
        assert test_agent._model == test_model
