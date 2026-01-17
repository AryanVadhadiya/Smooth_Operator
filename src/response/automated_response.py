"""
Automated response system - Executes security responses to threats
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseAction(Enum):
    """Types of automated responses"""
    ISOLATE_DEVICE = "isolate_device"
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    ROTATE_CREDENTIALS = "rotate_credentials"
    SERVICE_RESTART = "service_restart"
    SNAPSHOT_SYSTEM = "snapshot_system"
    QUARANTINE = "quarantine"
    NOTIFY_ADMIN = "notify_admin"


class ResponseStatus(Enum):
    """Response execution status"""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AutomatedResponseSystem:
    """Manages automated and semi-automated threat responses"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.response_actions_config = config.get('response_actions', [])
        self.auto_response_enabled = config.get('AUTO_RESPONSE_ENABLED', True)
        self.require_approval_p0 = config.get('REQUIRE_APPROVAL_P0', True)
        self.require_approval_p1 = config.get('REQUIRE_APPROVAL_P1', True)
        
        self.response_history = []
        self.pending_approvals = {}
        
    def determine_response_actions(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine appropriate response actions for an alert"""
        severity = alert['severity']
        sector = alert['sector']
        device_type = alert['device_type']
        
        actions = []
        
        # Always create a snapshot for critical alerts
        if severity in ['P0', 'P1']:
            actions.append({
                'action': ResponseAction.SNAPSHOT_SYSTEM.value,
                'target': alert['device_id'],
                'reason': 'Pre-response system snapshot',
                'requires_approval': False
            })
        
        # Sector-specific responses
        if sector == 'healthcare':
            actions.extend(self._healthcare_response_logic(alert))
        elif sector == 'agriculture':
            actions.extend(self._agriculture_response_logic(alert))
        elif sector == 'urban':
            actions.extend(self._urban_response_logic(alert))
        
        # General responses based on severity
        if severity == 'P0':
            actions.append({
                'action': ResponseAction.ISOLATE_DEVICE.value,
                'target': alert['device_id'],
                'reason': 'Critical threat detected',
                'requires_approval': self.require_approval_p0
            })
            actions.append({
                'action': ResponseAction.NOTIFY_ADMIN.value,
                'target': 'security_team',
                'reason': 'Critical alert requires immediate attention',
                'requires_approval': False
            })
        
        elif severity == 'P1':
            actions.append({
                'action': ResponseAction.RATE_LIMIT.value,
                'target': alert['device_id'],
                'reason': 'High-severity threat mitigation',
                'requires_approval': self.require_approval_p1
            })
        
        return actions
    
    def _healthcare_response_logic(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Healthcare-specific response logic"""
        actions = []
        device_type = alert['device_type']
        
        # For life-critical devices, only notify - don't auto-isolate
        life_critical = ['infusion_pump', 'ventilator', 'patient_monitor']
        
        if device_type in life_critical:
            actions.append({
                'action': ResponseAction.NOTIFY_ADMIN.value,
                'target': 'clinical_engineering',
                'reason': 'Life-critical device anomaly - manual intervention required',
                'requires_approval': False,
                'priority': 'urgent'
            })
        else:
            # Non-life-critical devices can be isolated
            if alert['severity'] in ['P0', 'P1']:
                actions.append({
                    'action': ResponseAction.QUARANTINE.value,
                    'target': alert['device_id'],
                    'reason': 'Isolate compromised healthcare device',
                    'requires_approval': True
                })
        
        # Check for data exfiltration
        raw_data = alert.get('raw_data', {})
        if raw_data.get('network_traffic_mbps', 0) > 200:
            actions.append({
                'action': ResponseAction.RATE_LIMIT.value,
                'target': alert['device_id'],
                'reason': 'Potential data exfiltration detected',
                'requires_approval': False
            })
        
        return actions
    
    def _agriculture_response_logic(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Agriculture-specific response logic"""
        actions = []
        device_type = alert['device_type']
        raw_data = alert.get('raw_data', {})
        
        # For irrigation controllers with anomalies, stop water flow
        if device_type == 'irrigation_controller' and alert['severity'] in ['P0', 'P1']:
            actions.append({
                'action': ResponseAction.SERVICE_RESTART.value,
                'target': alert['device_id'],
                'reason': 'Reset irrigation controller to safe defaults',
                'requires_approval': True
            })
        
        # For GPS spoofing, ground drones
        if device_type == 'drone' and 'gps' in str(raw_data):
            actions.append({
                'action': ResponseAction.ISOLATE_DEVICE.value,
                'target': alert['device_id'],
                'reason': 'GPS anomaly detected - ground drone',
                'requires_approval': False
            })
        
        # For fertilizer/chemical systems, halt operations
        if device_type == 'fertilizer_dispenser' and alert['severity'] == 'P0':
            actions.append({
                'action': ResponseAction.SERVICE_RESTART.value,
                'target': alert['device_id'],
                'reason': 'Chemical system anomaly - safety shutdown',
                'requires_approval': False
            })
        
        return actions
    
    def _urban_response_logic(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Urban systems-specific response logic"""
        actions = []
        device_type = alert['device_type']
        
        # For SCADA systems, never auto-isolate - human approval required
        scada_systems = ['water_treatment_scada', 'power_grid_monitor']
        
        if device_type in scada_systems:
            actions.append({
                'action': ResponseAction.NOTIFY_ADMIN.value,
                'target': 'scada_operators',
                'reason': 'Critical infrastructure anomaly - operator intervention required',
                'requires_approval': False,
                'priority': 'critical'
            })
            if alert['severity'] == 'P0':
                actions.append({
                    'action': ResponseAction.SNAPSHOT_SYSTEM.value,
                    'target': alert['device_id'],
                    'reason': 'Forensic capture before response',
                    'requires_approval': False
                })
        
        # Traffic controllers - failsafe mode
        if device_type == 'traffic_controller' and alert['severity'] == 'P0':
            actions.append({
                'action': ResponseAction.SERVICE_RESTART.value,
                'target': alert['device_id'],
                'reason': 'Reset to failsafe timing',
                'requires_approval': True
            })
        
        # Emergency systems - never auto-respond
        if device_type == 'emergency_system':
            actions.append({
                'action': ResponseAction.NOTIFY_ADMIN.value,
                'target': 'emergency_management',
                'reason': 'Emergency system compromised',
                'requires_approval': False,
                'priority': 'critical'
            })
        
        return actions
    
    def execute_response(self, action: Dict[str, Any], alert: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a response action"""
        response_id = f"resp_{datetime.utcnow().timestamp()}"
        
        response_record = {
            'response_id': response_id,
            'alert_id': alert['alert_id'],
            'action': action['action'],
            'target': action['target'],
            'reason': action['reason'],
            'status': ResponseStatus.PENDING.value,
            'created_at': datetime.utcnow().isoformat(),
            'executed_at': None,
            'completed_at': None,
            'success': None,
            'output': None,
            'rollback_info': None
        }
        
        # Check if approval required
        if action.get('requires_approval', False):
            logger.info(f"Response {response_id} requires approval: {action['action']}")
            response_record['status'] = ResponseStatus.PENDING.value
            self.pending_approvals[response_id] = response_record
            self.response_history.append(response_record)
            return response_record
        
        # Auto-execute if enabled
        if not self.auto_response_enabled:
            logger.info(f"Auto-response disabled, queueing {response_id}")
            self.pending_approvals[response_id] = response_record
            self.response_history.append(response_record)
            return response_record
        
        # Execute the action
        return self._execute_action(response_record)
    
    def _execute_action(self, response_record: Dict[str, Any]) -> Dict[str, Any]:
        """Actually execute the response action"""
        response_record['status'] = ResponseStatus.EXECUTING.value
        response_record['executed_at'] = datetime.utcnow().isoformat()
        
        action_type = response_record['action']
        target = response_record['target']
        
        try:
            if action_type == ResponseAction.ISOLATE_DEVICE.value:
                output = self._isolate_device(target)
            elif action_type == ResponseAction.BLOCK_IP.value:
                output = self._block_ip(target)
            elif action_type == ResponseAction.RATE_LIMIT.value:
                output = self._apply_rate_limit(target)
            elif action_type == ResponseAction.ROTATE_CREDENTIALS.value:
                output = self._rotate_credentials(target)
            elif action_type == ResponseAction.SERVICE_RESTART.value:
                output = self._restart_service(target)
            elif action_type == ResponseAction.SNAPSHOT_SYSTEM.value:
                output = self._create_snapshot(target)
            elif action_type == ResponseAction.QUARANTINE.value:
                output = self._quarantine_device(target)
            elif action_type == ResponseAction.NOTIFY_ADMIN.value:
                output = self._notify_admin(target, response_record)
            else:
                output = f"Unknown action type: {action_type}"
                raise ValueError(output)
            
            response_record['status'] = ResponseStatus.COMPLETED.value
            response_record['success'] = True
            response_record['output'] = output
            logger.info(f"Response {response_record['response_id']} completed successfully")
            
        except Exception as e:
            response_record['status'] = ResponseStatus.FAILED.value
            response_record['success'] = False
            response_record['output'] = str(e)
            logger.error(f"Response {response_record['response_id']} failed: {e}")
        
        response_record['completed_at'] = datetime.utcnow().isoformat()
        
        if response_record not in self.response_history:
            self.response_history.append(response_record)
        
        return response_record
    
    def approve_response(self, response_id: str, approver: str = 'admin') -> Dict[str, Any]:
        """Approve a pending response"""
        if response_id not in self.pending_approvals:
            raise ValueError(f"Response {response_id} not found in pending approvals")
        
        response_record = self.pending_approvals[response_id]
        response_record['approved_by'] = approver
        response_record['approved_at'] = datetime.utcnow().isoformat()
        response_record['status'] = ResponseStatus.APPROVED.value
        
        # Execute the approved action
        result = self._execute_action(response_record)
        
        # Remove from pending
        del self.pending_approvals[response_id]
        
        return result
    
    def rollback_response(self, response_id: str) -> Dict[str, Any]:
        """Rollback a completed response action"""
        response = next((r for r in self.response_history if r['response_id'] == response_id), None)
        
        if not response:
            raise ValueError(f"Response {response_id} not found")
        
        if response['status'] != ResponseStatus.COMPLETED.value:
            raise ValueError(f"Can only rollback completed responses. Current status: {response['status']}")
        
        logger.info(f"Rolling back response {response_id}: {response['action']}")
        
        # Simulate rollback (in production, this would reverse the action)
        response['status'] = ResponseStatus.ROLLED_BACK.value
        response['rolled_back_at'] = datetime.utcnow().isoformat()
        
        return response
    
    # Simulated action implementations
    def _isolate_device(self, device_id: str) -> str:
        """Isolate device from network"""
        logger.info(f"Isolating device {device_id} from network")
        time.sleep(0.5)  # Simulate action
        return f"Device {device_id} isolated successfully. Network access revoked."
    
    def _block_ip(self, ip_address: str) -> str:
        """Block IP address at firewall"""
        logger.info(f"Blocking IP address {ip_address}")
        time.sleep(0.3)
        return f"IP {ip_address} blocked at firewall level."
    
    def _apply_rate_limit(self, device_id: str) -> str:
        """Apply rate limiting"""
        logger.info(f"Applying rate limit to {device_id}")
        time.sleep(0.2)
        return f"Rate limit applied to {device_id}: 100 req/min"
    
    def _rotate_credentials(self, device_id: str) -> str:
        """Rotate authentication credentials"""
        logger.info(f"Rotating credentials for {device_id}")
        time.sleep(0.5)
        return f"Credentials rotated for {device_id}. New credentials issued."
    
    def _restart_service(self, device_id: str) -> str:
        """Restart service"""
        logger.info(f"Restarting service on {device_id}")
        time.sleep(1.0)
        return f"Service on {device_id} restarted successfully."
    
    def _create_snapshot(self, device_id: str) -> str:
        """Create system snapshot"""
        logger.info(f"Creating snapshot of {device_id}")
        time.sleep(0.5)
        snapshot_id = f"snap_{int(time.time())}"
        return f"Snapshot {snapshot_id} created for {device_id}"
    
    def _quarantine_device(self, device_id: str) -> str:
        """Quarantine device"""
        logger.info(f"Quarantining device {device_id}")
        time.sleep(0.4)
        return f"Device {device_id} moved to quarantine VLAN."
    
    def _notify_admin(self, target: str, response_record: Dict[str, Any]) -> str:
        """Notify administrator"""
        logger.info(f"Sending admin notification to {target}")
        return f"Notification sent to {target}"
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """Get response execution statistics"""
        total_responses = len(self.response_history)
        completed = len([r for r in self.response_history if r['status'] == ResponseStatus.COMPLETED.value])
        failed = len([r for r in self.response_history if r['status'] == ResponseStatus.FAILED.value])
        pending = len(self.pending_approvals)
        
        # Calculate mean time to execute
        execution_times = []
        for response in self.response_history:
            if response.get('executed_at') and response.get('completed_at'):
                start = datetime.fromisoformat(response['executed_at'])
                end = datetime.fromisoformat(response['completed_at'])
                execution_times.append((end - start).total_seconds())
        
        mean_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Count by action type
        action_counts = {}
        for response in self.response_history:
            action = response['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            'total_responses': total_responses,
            'completed': completed,
            'failed': failed,
            'pending_approval': pending,
            'success_rate': (completed / total_responses * 100) if total_responses > 0 else 0,
            'mean_execution_time_seconds': mean_execution_time,
            'action_counts': action_counts
        }
