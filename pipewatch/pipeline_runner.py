"""Orchestrates pre/post hooks around monitor.run_pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.hooks import HookConfig, HookResult, run_hooks
from pipewatch.monitor import RunResult, run_pipeline
from pipewatch.config import Config

log = logging.getLogger(__name__)


@dataclass
class PipelineRunSummary:
    pre_results: List[HookResult]
    run_result: RunResult
    post_results: List[HookResult]
    failure_results: List[HookResult] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.run_result.succeeded


def run_with_hooks(
    command: str,
    cfg: Config,
    hook_cfg: Optional[HookConfig] = None,
    env: Optional[dict] = None,
) -> PipelineRunSummary:
    """Run pre-hooks, the pipeline, then post/failure hooks."""
    if hook_cfg is None:
        hook_cfg = HookConfig()

    timeout = hook_cfg.timeout

    log.info("Running %d pre-hook(s)", len(hook_cfg.pre))
    pre_results = run_hooks(hook_cfg.pre, timeout=timeout)

    run_result = run_pipeline(command, cfg, extra_env=env)

    log.info("Running %d post-hook(s)", len(hook_cfg.post))
    post_results = run_hooks(hook_cfg.post, timeout=timeout)

    failure_results: List[HookResult] = []
    if not run_result.succeeded:
        log.info("Pipeline failed — running %d failure hook(s)", len(hook_cfg.on_failure))
        failure_results = run_hooks(hook_cfg.on_failure, timeout=timeout)

    return PipelineRunSummary(
        pre_results=pre_results,
        run_result=run_result,
        post_results=post_results,
        failure_results=failure_results,
    )
