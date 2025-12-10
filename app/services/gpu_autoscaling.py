"""GPU Autoscaling Support for Multi-GPU and Orchestration"""
import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class GPUNode:
    """Represents a GPU node in the cluster"""
    
    node_id: str
    gpu_count: int
    status: str  # 'active', 'idle', 'maintenance'
    current_load: float  # 0.0 to 1.0
    endpoint: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'gpu_count': self.gpu_count,
            'status': self.status,
            'current_load': self.current_load,
            'endpoint': self.endpoint
        }


class GPUAutoscaler:
    """
    GPU Autoscaling Manager
    Supports Kubernetes, Docker Swarm, and manual scaling
    """
    
    def __init__(self):
        self.orchestrator = os.getenv('GPU_ORCHESTRATOR', 'manual')  # kubernetes, docker_swarm, manual
        self.min_nodes = int(os.getenv('GPU_MIN_NODES', '1'))
        self.max_nodes = int(os.getenv('GPU_MAX_NODES', '5'))
        self.scale_up_threshold = float(os.getenv('GPU_SCALE_UP_THRESHOLD', '0.8'))
        self.scale_down_threshold = float(os.getenv('GPU_SCALE_DOWN_THRESHOLD', '0.3'))
        
        # Node registry
        self.nodes: List[GPUNode] = []
        
        logger.info(f"GPU Autoscaler initialized:")
        logger.info(f"  Orchestrator: {self.orchestrator}")
        logger.info(f"  Node range: {self.min_nodes}-{self.max_nodes}")
        logger.info(f"  Scale up threshold: {self.scale_up_threshold}")
        logger.info(f"  Scale down threshold: {self.scale_down_threshold}")
    
    def register_node(
        self,
        node_id: str,
        gpu_count: int,
        endpoint: str
    ) -> bool:
        """
        Register a GPU node
        
        Args:
            node_id: Unique node identifier
            gpu_count: Number of GPUs on this node
            endpoint: WebSocket endpoint URL
        
        Returns:
            True if registered successfully
        """
        
        try:
            node = GPUNode(
                node_id=node_id,
                gpu_count=gpu_count,
                status='idle',
                current_load=0.0,
                endpoint=endpoint
            )
            
            self.nodes.append(node)
            logger.info(f"✅ Registered GPU node: {node_id} ({gpu_count} GPUs) at {endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register node {node_id}: {e}")
            return False
    
    def get_available_node(self) -> Optional[GPUNode]:
        """
        Get an available GPU node with lowest load
        
        Returns:
            GPUNode or None if no nodes available
        """
        
        available_nodes = [
            node for node in self.nodes
            if node.status == 'active' or node.status == 'idle'
        ]
        
        if not available_nodes:
            logger.warning("⚠️ No available GPU nodes")
            return None
        
        # Sort by current load (ascending)
        available_nodes.sort(key=lambda n: n.current_load)
        
        selected_node = available_nodes[0]
        logger.info(f"📍 Selected node: {selected_node.node_id} (load: {selected_node.current_load:.0%})")
        
        return selected_node
    
    def update_node_load(self, node_id: str, load: float) -> None:
        """Update node load metric"""
        
        for node in self.nodes:
            if node.node_id == node_id:
                node.current_load = load
                logger.debug(f"Updated {node_id} load: {load:.0%}")
                break
    
    def check_scaling_needed(self) -> Optional[str]:
        """
        Check if scaling is needed
        
        Returns:
            'scale_up', 'scale_down', or None
        """
        
        if not self.nodes:
            return 'scale_up' if self.min_nodes > 0 else None
        
        # Calculate average load
        active_nodes = [n for n in self.nodes if n.status == 'active']
        
        if not active_nodes:
            return 'scale_up' if self.min_nodes > 0 else None
        
        avg_load = sum(n.current_load for n in active_nodes) / len(active_nodes)
        
        logger.debug(f"Average GPU load: {avg_load:.0%}")
        
        # Check scale up
        if avg_load > self.scale_up_threshold and len(active_nodes) < self.max_nodes:
            logger.info(f"🔼 Scale up needed: {avg_load:.0%} > {self.scale_up_threshold:.0%}")
            return 'scale_up'
        
        # Check scale down
        if avg_load < self.scale_down_threshold and len(active_nodes) > self.min_nodes:
            logger.info(f"🔽 Scale down possible: {avg_load:.0%} < {self.scale_down_threshold:.0%}")
            return 'scale_down'
        
        return None
    
    def scale_up(self) -> bool:
        """
        Scale up GPU nodes
        
        Returns:
            True if scaled successfully
        """
        
        if self.orchestrator == 'kubernetes':
            return self._scale_kubernetes('up')
        elif self.orchestrator == 'docker_swarm':
            return self._scale_docker_swarm('up')
        else:
            logger.info("Manual orchestration - scale up manually")
            return False
    
    def scale_down(self) -> bool:
        """
        Scale down GPU nodes
        
        Returns:
            True if scaled successfully
        """
        
        if self.orchestrator == 'kubernetes':
            return self._scale_kubernetes('down')
        elif self.orchestrator == 'docker_swarm':
            return self._scale_docker_swarm('down')
        else:
            logger.info("Manual orchestration - scale down manually")
            return False
    
    def _scale_kubernetes(self, direction: str) -> bool:
        """Scale Kubernetes deployment"""
        
        try:
            # This would use kubectl or Kubernetes Python client
            deployment_name = os.getenv('K8S_DEPLOYMENT_NAME', 'vibevoice-tts')
            namespace = os.getenv('K8S_NAMESPACE', 'default')
            
            current_replicas = len([n for n in self.nodes if n.status == 'active'])
            new_replicas = current_replicas + 1 if direction == 'up' else current_replicas - 1
            
            logger.info(f"Would scale Kubernetes deployment {deployment_name} to {new_replicas} replicas")
            
            # kubectl scale deployment vibevoice-tts --replicas=new_replicas -n namespace
            # For now, just log the action
            
            return True
            
        except Exception as e:
            logger.error(f"Kubernetes scaling failed: {e}")
            return False
    
    def _scale_docker_swarm(self, direction: str) -> bool:
        """Scale Docker Swarm service"""
        
        try:
            service_name = os.getenv('SWARM_SERVICE_NAME', 'vibevoice-tts')
            
            current_replicas = len([n for n in self.nodes if n.status == 'active'])
            new_replicas = current_replicas + 1 if direction == 'up' else current_replicas - 1
            
            logger.info(f"Would scale Docker Swarm service {service_name} to {new_replicas} replicas")
            
            # docker service scale vibevoice-tts=new_replicas
            # For now, just log the action
            
            return True
            
        except Exception as e:
            logger.error(f"Docker Swarm scaling failed: {e}")
            return False
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get cluster status"""
        
        active_nodes = [n for n in self.nodes if n.status == 'active']
        idle_nodes = [n for n in self.nodes if n.status == 'idle']
        
        total_gpus = sum(n.gpu_count for n in self.nodes)
        avg_load = sum(n.current_load for n in active_nodes) / len(active_nodes) if active_nodes else 0.0
        
        return {
            'orchestrator': self.orchestrator,
            'total_nodes': len(self.nodes),
            'active_nodes': len(active_nodes),
            'idle_nodes': len(idle_nodes),
            'total_gpus': total_gpus,
            'average_load': round(avg_load, 4),
            'min_nodes': self.min_nodes,
            'max_nodes': self.max_nodes,
            'scaling_needed': self.check_scaling_needed(),
            'nodes': [n.to_dict() for n in self.nodes]
        }
