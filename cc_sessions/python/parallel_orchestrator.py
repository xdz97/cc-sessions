#!/usr/bin/env python3
"""
Parallel Agent Orchestrator

Manages execution of multiple Task agents simultaneously to parallelize work.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import from hooks
from cc_sessions.python.hooks.shared_state import PROJECT_ROOT


class AgentStatus(str, Enum):
    """Status of a parallel agent task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """Represents a single agent task in parallel execution"""
    id: str
    agent_name: str
    prompt: str
    status: AgentStatus = AgentStatus.PENDING
    process_id: Optional[int] = None
    output: str = ""
    error: str = ""
    exit_code: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'agent_name': self.agent_name,
            'prompt': self.prompt,
            'status': self.status.value,
            'process_id': self.process_id,
            'output': self.output,
            'error': self.error,
            'exit_code': self.exit_code,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration
        }


@dataclass
class OrchestrationResult:
    """Result of parallel orchestration execution"""
    total_tasks: int
    completed: int
    failed: int
    total_duration: float
    tasks: List[AgentTask] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'total_tasks': self.total_tasks,
            'completed': self.completed,
            'failed': self.failed,
            'total_duration': self.total_duration,
            'tasks': [task.to_dict() for task in self.tasks]
        }

    def __str__(self) -> str:
        """Human-readable summary"""
        lines = [
            f"\n=== Parallel Orchestration Results ===",
            f"Total Tasks: {self.total_tasks}",
            f"Completed: {self.completed}",
            f"Failed: {self.failed}",
            f"Total Duration: {self.total_duration:.2f}s",
            f"\nIndividual Task Results:"
        ]

        for task in self.tasks:
            status_symbol = "✓" if task.status == AgentStatus.COMPLETED else "✗"
            duration_str = f"{task.duration:.2f}s" if task.duration else "N/A"
            lines.append(f"  {status_symbol} {task.agent_name} ({task.id}): {task.status.value} - {duration_str}")

        return "\n".join(lines)


class ParallelAgentOrchestrator:
    """
    Orchestrates multiple Task agents to run in parallel.

    This allows complex operations like code review to be split across
    multiple agents analyzing different files/modules simultaneously.
    """

    def __init__(self, max_concurrent: int = 4):
        """
        Initialize the orchestrator.

        Args:
            max_concurrent: Maximum number of agents to run simultaneously
        """
        self.max_concurrent = max_concurrent
        self.tasks: List[AgentTask] = []
        self.running_tasks: List[AgentTask] = []

    def add_task(self, agent_name: str, prompt: str, task_id: Optional[str] = None) -> AgentTask:
        """
        Add a task to the orchestration queue.

        Args:
            agent_name: Name of the agent to invoke (e.g., 'code-review', 'context-gathering')
            prompt: The prompt to send to the agent
            task_id: Optional custom ID for the task

        Returns:
            The created AgentTask
        """
        if not task_id:
            task_id = f"{agent_name}_{len(self.tasks) + 1}"

        task = AgentTask(
            id=task_id,
            agent_name=agent_name,
            prompt=prompt
        )
        self.tasks.append(task)
        return task

    def _start_agent_process(self, task: AgentTask) -> subprocess.Popen:
        """
        Start a Task agent process for the given task.

        Args:
            task: The task to execute

        Returns:
            The subprocess.Popen object
        """
        # TODO: This needs to invoke the Claude Code Task tool
        # For now, this is a placeholder that would need integration with Claude Code's API
        # In practice, this would call out to Claude Code's agent execution system

        # Placeholder command - would actually invoke Task tool through Claude Code
        command = [
            'echo',
            f"[PLACEHOLDER] Running agent {task.agent_name} with prompt: {task.prompt[:50]}..."
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        task.process_id = process.pid
        task.status = AgentStatus.RUNNING
        task.start_time = time.time()

        return process

    def _poll_running_tasks(self) -> None:
        """Check status of running tasks and move completed ones."""
        completed = []

        for task in self.running_tasks:
            # In real implementation, would check actual process status
            # For now, simulate completion
            task.status = AgentStatus.COMPLETED
            task.end_time = time.time()
            task.exit_code = 0
            completed.append(task)

        # Remove completed tasks from running list
        for task in completed:
            self.running_tasks.remove(task)

    def execute_all(self, timeout: Optional[float] = None) -> OrchestrationResult:
        """
        Execute all queued tasks in parallel.

        Args:
            timeout: Optional timeout in seconds for the entire orchestration

        Returns:
            OrchestrationResult with execution summary
        """
        start_time = time.time()
        pending_tasks = [t for t in self.tasks if t.status == AgentStatus.PENDING]

        while pending_tasks or self.running_tasks:
            # Check for timeouts
            if timeout and (time.time() - start_time) > timeout:
                # Mark all pending/running tasks as failed
                for task in pending_tasks + self.running_tasks:
                    if task.status in (AgentStatus.PENDING, AgentStatus.RUNNING):
                        task.status = AgentStatus.FAILED
                        task.error = "Timeout exceeded"
                        task.end_time = time.time()
                break

            # Start new tasks up to max_concurrent limit
            while len(self.running_tasks) < self.max_concurrent and pending_tasks:
                task = pending_tasks.pop(0)
                try:
                    self._start_agent_process(task)
                    self.running_tasks.append(task)
                except Exception as e:
                    task.status = AgentStatus.FAILED
                    task.error = str(e)
                    task.end_time = time.time()

            # Poll running tasks for completion
            self._poll_running_tasks()

            # Small sleep to avoid busy-waiting
            if self.running_tasks:
                time.sleep(0.1)

        # Calculate results
        total_duration = time.time() - start_time
        completed = sum(1 for t in self.tasks if t.status == AgentStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == AgentStatus.FAILED)

        return OrchestrationResult(
            total_tasks=len(self.tasks),
            completed=completed,
            failed=failed,
            total_duration=total_duration,
            tasks=self.tasks.copy()
        )

    def execute_and_wait(self, task_definitions: List[Tuple[str, str]]) -> OrchestrationResult:
        """
        Convenience method to add tasks and execute them immediately.

        Args:
            task_definitions: List of (agent_name, prompt) tuples

        Returns:
            OrchestrationResult with execution summary

        Example:
            orchestrator = ParallelAgentOrchestrator(max_concurrent=3)
            result = orchestrator.execute_and_wait([
                ('code-review', 'Review src/auth/'),
                ('code-review', 'Review src/api/'),
                ('code-review', 'Review src/database/')
            ])
        """
        for agent_name, prompt in task_definitions:
            self.add_task(agent_name, prompt)

        return self.execute_all()


def parallel_code_review(file_paths: List[str], max_concurrent: int = 3) -> OrchestrationResult:
    """
    Perform parallel code review across multiple files/directories.

    Args:
        file_paths: List of file or directory paths to review
        max_concurrent: Maximum number of reviews to run in parallel

    Returns:
        OrchestrationResult with all review results

    Example:
        result = parallel_code_review([
            'src/auth/',
            'src/api/',
            'src/database/'
        ])
        print(result)
    """
    orchestrator = ParallelAgentOrchestrator(max_concurrent=max_concurrent)

    for path in file_paths:
        prompt = f"Perform a thorough code review of {path}. Focus on security, performance, and code quality."
        orchestrator.add_task('code-review', prompt, task_id=f"review_{Path(path).name}")

    return orchestrator.execute_all()


def parallel_context_gathering(task_files: List[str], max_concurrent: int = 3) -> OrchestrationResult:
    """
    Gather context for multiple tasks in parallel.

    Args:
        task_files: List of task file paths
        max_concurrent: Maximum number of context gatherings to run in parallel

    Returns:
        OrchestrationResult with all context gathering results

    Example:
        result = parallel_context_gathering([
            'sessions/tasks/h-implement-auth.md',
            'sessions/tasks/m-add-logging.md'
        ])
    """
    orchestrator = ParallelAgentOrchestrator(max_concurrent=max_concurrent)

    for task_file in task_files:
        task_path = Path(task_file)
        prompt = f"Create a comprehensive context manifest for the task in {task_file}"
        orchestrator.add_task('context-gathering', prompt, task_id=f"context_{task_path.stem}")

    return orchestrator.execute_all()


# Example usage and testing
if __name__ == "__main__":
    # Example: Parallel code review
    print("=== Example: Parallel Code Review ===")
    result = parallel_code_review([
        'cc_sessions/python/hooks/',
        'cc_sessions/python/api/',
        'cc_sessions/protocols/'
    ], max_concurrent=2)
    print(result)

    # Example: Custom orchestration
    print("\n=== Example: Custom Orchestration ===")
    orchestrator = ParallelAgentOrchestrator(max_concurrent=3)
    orchestrator.add_task('code-review', 'Review authentication module')
    orchestrator.add_task('code-review', 'Review API endpoints')
    orchestrator.add_task('logging', 'Consolidate task logs')

    result = orchestrator.execute_all()
    print(result)
    print(f"\nJSON output:\n{json.dumps(result.to_dict(), indent=2)}")
