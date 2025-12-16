"""Test fixtures for jmx_to_scenario tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def minimal_jmx() -> str:
    """Return minimal valid JMX content."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan" enabled="true">
      <boolProp name="TestPlan.functional_mode">false</boolProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">0</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GET /api/test" enabled="true">
          <stringProp name="HTTPSampler.domain">example.com</stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.path">/api/test</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''


@pytest.fixture
def jmx_with_capture() -> str:
    """Return JMX content with JSONPostProcessor."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan" enabled="true"/>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">0</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Create User" enabled="true">
          <stringProp name="HTTPSampler.domain">api.example.com</stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.path">/users</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <stringProp name="Argument.value">{"name": "test"}</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
        </HTTPSamplerProxy>
        <hashTree>
          <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="Extract userId" enabled="true">
            <stringProp name="JSONPostProcessor.referenceNames">userId</stringProp>
            <stringProp name="JSONPostProcessor.jsonPathExprs">$.id</stringProp>
            <stringProp name="JSONPostProcessor.match_numbers">1</stringProp>
          </JSONPostProcessor>
          <hashTree/>
        </hashTree>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''


@pytest.fixture
def temp_jmx_file(minimal_jmx: str) -> Path:
    """Create a temporary JMX file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jmx", delete=False) as f:
        f.write(minimal_jmx)
        return Path(f.name)


@pytest.fixture
def temp_jmx_file_with_capture(jmx_with_capture: str) -> Path:
    """Create a temporary JMX file with capture."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jmx", delete=False) as f:
        f.write(jmx_with_capture)
        return Path(f.name)


@pytest.fixture
def jmx_with_file_upload() -> str:
    """Return JMX content with HTTPFileArgs."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan" enabled="true"/>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">0</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Upload File" enabled="true">
          <stringProp name="HTTPSampler.domain">api.example.com</stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.path">/upload</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <elementProp name="HTTPsampler.Files" elementType="HTTPFileArgs">
            <collectionProp name="HTTPFileArgs.files">
              <elementProp name="document.pdf" elementType="HTTPFileArg">
                <stringProp name="File.path">document.pdf</stringProp>
                <stringProp name="File.paramname">file</stringProp>
                <stringProp name="File.mimetype">application/pdf</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''


@pytest.fixture
def jmx_with_multiple_files() -> str:
    """Return JMX content with multiple HTTPFileArgs."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan" enabled="true"/>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">0</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Upload Multiple" enabled="true">
          <stringProp name="HTTPSampler.domain">api.example.com</stringProp>
          <stringProp name="HTTPSampler.path">/upload-multiple</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <elementProp name="HTTPsampler.Files" elementType="HTTPFileArgs">
            <collectionProp name="HTTPFileArgs.files">
              <elementProp name="report.pdf" elementType="HTTPFileArg">
                <stringProp name="File.path">reports/report.pdf</stringProp>
                <stringProp name="File.paramname">document</stringProp>
                <stringProp name="File.mimetype">application/pdf</stringProp>
              </elementProp>
              <elementProp name="image.png" elementType="HTTPFileArg">
                <stringProp name="File.path">${image_path}</stringProp>
                <stringProp name="File.paramname">image</stringProp>
                <stringProp name="File.mimetype">image/png</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''


@pytest.fixture
def temp_jmx_file_with_file_upload(jmx_with_file_upload: str) -> Path:
    """Create a temporary JMX file with file upload."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jmx", delete=False) as f:
        f.write(jmx_with_file_upload)
        return Path(f.name)


@pytest.fixture
def temp_jmx_file_with_multiple_files(jmx_with_multiple_files: str) -> Path:
    """Create a temporary JMX file with multiple files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jmx", delete=False) as f:
        f.write(jmx_with_multiple_files)
        return Path(f.name)


@pytest.fixture
def jmx_with_random_controller() -> str:
    """Return JMX content with RandomController."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan" enabled="true"/>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">0</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <RandomController guiclass="RandomControlPanel" testclass="RandomController" testname="Random Selection" enabled="true"/>
        <hashTree>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Option A" enabled="true">
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <stringProp name="HTTPSampler.path">/api/option-a</stringProp>
          </HTTPSamplerProxy>
          <hashTree/>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Option B" enabled="true">
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <stringProp name="HTTPSampler.path">/api/option-b</stringProp>
          </HTTPSamplerProxy>
          <hashTree/>
        </hashTree>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''


@pytest.fixture
def jmx_with_test_action() -> str:
    """Return JMX content with TestAction (pause)."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan" enabled="true"/>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">0</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="First Request" enabled="true">
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <stringProp name="HTTPSampler.path">/api/first</stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
        <TestAction guiclass="TestActionGui" testclass="TestAction" testname="Pause 2s" enabled="true">
          <intProp name="TestAction.action">1</intProp>
          <intProp name="TestAction.target">0</intProp>
          <stringProp name="TestAction.duration">2000</stringProp>
        </TestAction>
        <hashTree/>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Second Request" enabled="true">
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <stringProp name="HTTPSampler.path">/api/second</stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''


@pytest.fixture
def jmx_with_transaction_controller() -> str:
    """Return JMX content with TransactionController."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test Plan" enabled="true"/>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">0</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <TransactionController guiclass="TransactionControllerGui" testclass="TransactionController" testname="Login Flow" enabled="true">
          <boolProp name="TransactionController.includeTimers">false</boolProp>
        </TransactionController>
        <hashTree>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Get Login Page" enabled="true">
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <stringProp name="HTTPSampler.path">/login</stringProp>
          </HTTPSamplerProxy>
          <hashTree/>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Submit Login" enabled="true">
            <stringProp name="HTTPSampler.method">POST</stringProp>
            <stringProp name="HTTPSampler.path">/auth</stringProp>
          </HTTPSamplerProxy>
          <hashTree/>
        </hashTree>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''


@pytest.fixture
def temp_jmx_file_with_random_controller(jmx_with_random_controller: str) -> Path:
    """Create a temporary JMX file with RandomController."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jmx", delete=False) as f:
        f.write(jmx_with_random_controller)
        return Path(f.name)


@pytest.fixture
def temp_jmx_file_with_test_action(jmx_with_test_action: str) -> Path:
    """Create a temporary JMX file with TestAction."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jmx", delete=False) as f:
        f.write(jmx_with_test_action)
        return Path(f.name)


@pytest.fixture
def temp_jmx_file_with_transaction_controller(jmx_with_transaction_controller: str) -> Path:
    """Create a temporary JMX file with TransactionController."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jmx", delete=False) as f:
        f.write(jmx_with_transaction_controller)
        return Path(f.name)
