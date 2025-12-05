# Implementation Plan: Prompts Telemetry Support

## Goal

Update the Shinzo SDK to support telemetry for MCP Prompts, enabling data export to OTel-compatible services. This will allow developers to track prompt usage (frequency, specific prompts used, arguments) similar to how Tools and Resources are currently tracked.

## Proposed Changes

### 1. Update `src/shinzo/session.py`

**Objective**: Extensions to `EventType` enum to support prompt operations.

- **Modify `EventType` enum**:
  - Add `PROMPT_GET` (or `PROMPT_EXECUTION`) to track when a specific prompt is retrieved/executed.
  - Add `PROMPT_LIST` to track when the list of available prompts is requested.

```python
class EventType(str, Enum):
    # ... existing events ...
    PROMPT_GET = "prompt_get"   # For prompts/get
    PROMPT_LIST = "prompt_list" # For prompts/list
```

### 2. Update `src/shinzo/instrumentation.py`

**Objective**: Implement the instrumentation logic for Prompts in `McpServerInstrumentation`.

- **Enable Prompt Instrumentation**:

  - In the `instrument` method, uncomment (or add) the call to `self._instrument_prompts()`.

- **Implement `_instrument_prompts` method**:
  - This method will determine if the server uses the FastMCP pattern (decorators) or Traditional MCP pattern (methods on the server instance) and call the appropriate sub-method.

```python
    def _instrument_prompts(self) -> None:
        """Instrument prompt operations."""
        # Check for FastMCP style (if applicable, though FastMCP usually registers defined prompts)
        if hasattr(self.server, "prompt"):
             self._instrument_fastmcp_prompts()

        # Check for Traditional MCP style
        if hasattr(self.server, "get_prompt") or hasattr(self.server, "list_prompts"):
            self._instrument_traditional_prompts()
```

- **Implement `_instrument_fastmcp_prompts`**:

  - Similar to `_instrument_fastmcp_tools`, wrap the `self.server.prompt` decorator to intercept prompt registration and wrap the prompt handler.
  - _Note_: Verify if FastMCP `server.prompt` returns a decorator that wraps the function. If so, wrapping it allows us to instrument the execution of that prompt function.

- **Implement `_instrument_traditional_prompts`**:

  - Wrap `self.server.get_prompt`:
    - Method: `prompts/get`
    - Name: Dynamic (based on the `name` argument passed to `get_prompt`). _Note_: Usually `get_prompt` takes `name` as an argument. The generic `_create_instrumented_handler` might need adjustment or we might need a specific wrapper for `get_prompt` to extract the prompt name from arguments for the span name/attributes.
  - Wrap `self.server.list_prompts`:
    - Method: `prompts/list`
    - Name: "list_prompts"

- **Refine `_create_instrumented_handler` or Create Specific Wrappers**:
  - The current `_create_instrumented_handler` assumes the function name is the tool name. For `get_prompt(name, ...)`, the "tool name" concept maps to the "prompt name", which is an _argument_, not the function name itself.
  - We may need a specialized wrapper for `get_prompt` that looks at the first argument (`name`) to populate `mcp.prompt.name` attribute and `tool_name` in `SessionEvent`.

### 3. Telemetry Schema & Attributes

Follow the **OpenTelemetry Semantic Conventions for MCP** as proposed in [PR #2083](https://github.com/open-telemetry/semantic-conventions/pull/2083).

- **General Attributes**:

  - `gen_ai.system`: `mcp` (To identify the system as MCP)
  - `mcp.method.name`: The MCP method being called (e.g., `prompts/get`, `prompts/list`)

- **`prompts/get`**:

  - **Span Name**: `prompts/get <prompt_name>`
  - **Attributes**:
    - `mcp.method.name`: `prompts/get`
    - `mcp.prompt.name`: `<prompt_name>` (The name of the prompt being retrieved)
    - `mcp.prompt.arguments`: JSON string of arguments provided to the prompt.
  - **Session Event**:
    - `event_type`: `PROMPT_GET`
    - `tool_name`: `<prompt_name>` (Mapped to prompt name for consistency)
    - `input_data`: arguments

- **`prompts/list`**:
  - **Span Name**: `prompts/list`
  - **Attributes**:
    - `mcp.method.name`: `prompts/list`
  - **Session Event**:
    - `event_type`: `PROMPT_LIST`

## Verification Plan

1.  **Create a Test Script**:

    - Create a script (e.g., `test_prompts_instrumentation.py`) that sets up a dummy MCP server with defined prompts.
    - Configure the server with `instrument_server`.
    - Mock the `TelemetryManager` or check the `SessionTracker` output.
    - Call `list_prompts()` and `get_prompt("test_prompt", arguments={...})`.
    - Assert that `SessionEvent`s are created with correct types (`PROMPT_LIST`, `PROMPT_GET`) and data.
    - Assert that OTel spans are created.

2.  **Integrate with Existing Tests**:
    - Run existing tests to ensure no regression in Tool usage.

## Code Snippets (Mental Draft)

**Wrapper for `get_prompt`**:

```python
        original_get_prompt = self.server.get_prompt

        @functools.wraps(original_get_prompt)
        async def instrumented_get_prompt(name: str, **kwargs) -> Any:
            # Setup attributes
            attributes = {
                "mcp.method.name": "prompts/get",
                "mcp.prompt.name": name
            }
            # Start Span, Record Metric...
            # Add Session Event
            # Call original
            result = await original_get_prompt(name, **kwargs)
            # End Span, Record Duration...
            return result

        self.server.get_prompt = instrumented_get_prompt
```
