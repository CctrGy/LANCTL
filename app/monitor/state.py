from __future__ import annotations
from .models import CheckResult,DeviceState,MonitorProfile,now_iso

class StateEvaluator:
    def __init__(self,profile:MonitorProfile):self.profile=profile;self.states={}
    def evaluate(self,result:CheckResult):
        state=self.states.setdefault(result.target,DeviceState(result.target)); before=(state.presence,state.health)
        if result.checkId=="availability":
            if result.success:
                state.consecutiveRecoveries+=1;state.consecutiveFailures=0
                if state.consecutiveRecoveries>=self.profile.recovery_threshold:state.presence="online"
            else:
                state.consecutiveFailures+=1;state.consecutiveRecoveries=0
                if state.consecutiveFailures>=self.profile.failure_threshold:state.presence="offline"
        elif not result.success:state.health="warning"
        elif state.health!="maintenance":state.health="healthy"
        latency=result.latencyMs
        if latency is not None: state.health="critical" if latency>=1000 else "warning" if latency>=250 else state.health
        state.updatedAt=now_iso(); return state,before!=(state.presence,state.health),before
