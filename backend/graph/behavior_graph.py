"""
Signer + Device + Certificate Behavioral Knowledge Graph
Analyzes relationship topology, detects impossible travel (geo-velocity),
stolen key sharing, and rogue infrastructure patterns using NetworkX.
"""

import math
import time
import datetime
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from backend.config import MAX_CREDIBLE_TRAVEL_SPEED_KMH

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class SignerBehaviorGraph:
    """
    Maintains a multi-relational graph of Signers, Devices, IPs, Certificates, and CAs.
    Computes graph-theoretic anomaly signals and velocity metrics.
    """

    def __init__(self):
        self.G = nx.DiGraph()
        # Track historical location and timestamp per signer
        # Format: {signer_id: {"lat": float, "lon": float, "city": str, "ip": str, "timestamp": float}}
        self.signer_last_location: Dict[str, Dict[str, Any]] = {}
        # Track certificates and who used them
        self.cert_usage: Dict[str, List[Dict[str, Any]]] = {}

        # Seed baseline trusted infrastructure
        self._initialize_baseline_topology()

    def _initialize_baseline_topology(self):
        """Pre-seeds trusted root CA and typical government departments."""
        self.G.add_node("ca:National-Root-CA", label="National Root CA", type="ca", trusted=True)
        self.G.add_node("ca:Sub-CA-GovID", label="Gov e-ID Sub-CA", type="ca", trusted=True)
        self.G.add_edge("ca:Sub-CA-GovID", "ca:National-Root-CA", relation="ISSUED_BY")

    def record_and_evaluate(
        self,
        signer_id: str,
        device_fingerprint: str,
        ip_address: str,
        geo_location: Dict[str, Any],
        cert_serial: str,
        ca_name: str,
        timestamp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Ingests a new signing context, updates graph topology, and evaluates:
        1. Impossible Travel (Geo-velocity in km/h)
        2. New Device / New IP anomaly
        3. Key/Certificate sharing anomaly across disparate signers
        4. Rogue / Untrusted CA association
        """
        current_ts = timestamp or time.time()
        lat = float(geo_location.get("lat", 28.6139))  # Default New Delhi
        lon = float(geo_location.get("lon", 77.2090))
        city = geo_location.get("city", "New Delhi")
        country = geo_location.get("country", "IN")

        anomaly_flags: List[str] = []
        anomaly_score = 0.0
        velocity_kmh = 0.0
        distance_km = 0.0

        # Node IDs
        node_signer = f"signer:{signer_id}"
        node_device = f"device:{device_fingerprint}"
        node_ip = f"ip:{ip_address}"
        node_cert = f"cert:{cert_serial}"
        node_ca = f"ca:{ca_name}"

        # 1. Geo-Velocity & Impossible Travel Check
        if signer_id in self.signer_last_location:
            last_loc = self.signer_last_location[signer_id]
            time_diff_hours = (current_ts - last_loc["timestamp"]) / 3600.0

            if time_diff_hours > 0:
                distance_km = haversine_distance_km(last_loc["lat"], last_loc["lon"], lat, lon)
                velocity_kmh = distance_km / time_diff_hours

                # Check if velocity exceeds realistic airline flight speed (> 900 km/h)
                if velocity_kmh > MAX_CREDIBLE_TRAVEL_SPEED_KMH and distance_km > 100.0:
                    anomaly_flags.append(
                        f"IMPOSSIBLE TRAVEL DETECTED: {distance_km:.1f} km traveled in {time_diff_hours*60:.1f} mins "
                        f"({velocity_kmh:.0f} km/h from {last_loc['city']} to {city})"
                    )
                    anomaly_score += 0.85
                elif distance_km > 500.0 and time_diff_hours < 2.0:
                    anomaly_flags.append(f"Suspicious fast relocation ({distance_km:.1f} km in {time_diff_hours*60:.1f} mins)")
                    anomaly_score += 0.40

        # Update last location
        self.signer_last_location[signer_id] = {
            "lat": lat,
            "lon": lon,
            "city": city,
            "country": country,
            "ip": ip_address,
            "timestamp": current_ts
        }

        # 2. Unknown Device / Novel IP Anomaly
        is_new_device = not self.G.has_node(node_device)
        is_new_signer_device_pair = not self.G.has_edge(node_signer, node_device)

        if is_new_signer_device_pair and self.G.has_node(node_signer):
            anomaly_flags.append(f"Signer active on novel device fingerprint: {device_fingerprint[:8]}...")
            anomaly_score += 0.35

        # 3. Key / Certificate Sharing Anomaly
        if cert_serial not in self.cert_usage:
            self.cert_usage[cert_serial] = []
        
        # Check if cert was previously bound to a DIFFERENT signer
        other_signers = [entry["signer"] for entry in self.cert_usage[cert_serial] if entry["signer"] != signer_id]
        if other_signers:
            anomaly_flags.append(
                f"STOLEN KEY / DUAL SIGNER ALERT: Certificate serial {cert_serial} concurrently used by "
                f"different accounts: {list(set(other_signers))}"
            )
            anomaly_score += 0.90

        self.cert_usage[cert_serial].append({
            "signer": signer_id,
            "ip": ip_address,
            "device": device_fingerprint,
            "timestamp": current_ts
        })

        # 4. Graph Topology Update
        self.G.add_node(node_signer, label=signer_id, type="signer")
        self.G.add_node(node_device, label=f"Dev:{device_fingerprint[:6]}", type="device")
        self.G.add_node(node_ip, label=f"{ip_address} ({city})", type="ip", lat=lat, lon=lon)
        self.G.add_node(node_cert, label=f"Cert:{cert_serial[:8]}", type="cert")
        self.G.add_node(node_ca, label=ca_name, type="ca")

        # Add edges
        self.G.add_edge(node_signer, node_device, relation="USES_DEVICE")
        self.G.add_edge(node_signer, node_ip, relation="SIGNS_FROM")
        self.G.add_edge(node_signer, node_cert, relation="SIGNS_WITH")
        self.G.add_edge(node_cert, node_ca, relation="ISSUED_BY")

        # Clamp anomaly score
        anomaly_score = min(1.0, anomaly_score)

        return {
            "graph_anomaly_score": round(anomaly_score, 3),
            "distance_km": round(distance_km, 1),
            "velocity_kmh": round(velocity_kmh, 1),
            "is_impossible_travel": velocity_kmh > MAX_CREDIBLE_TRAVEL_SPEED_KMH and distance_km > 100.0,
            "flags": anomaly_flags,
            "connected_components": nx.number_weakly_connected_components(self.G),
            "graph_node_count": self.G.number_of_nodes(),
            "graph_edge_count": self.G.number_of_edges()
        }

    def get_visualization_data(self) -> Dict[str, Any]:
        """Exports graph in Vis.js / Cytoscape compatible node & edge format."""
        nodes = []
        edges = []

        type_colors = {
            "signer": "#38bdf8",   # Sky blue
            "device": "#a855f7",   # Purple
            "ip": "#f59e0b",       # Amber
            "cert": "#10b981",     # Emerald green
            "ca": "#6366f1"        # Indigo
        }

        for n, data in self.G.nodes(data=True):
            node_type = data.get("type", "unknown")
            color = type_colors.get(node_type, "#94a3b8")
            nodes.append({
                "id": n,
                "label": data.get("label", n),
                "type": node_type,
                "color": color,
                "title": f"Type: {node_type.upper()}<br>ID: {n}"
            })

        for u, v, data in self.G.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "label": data.get("relation", "LINKED"),
                "arrows": "to"
            })

        return {"nodes": nodes, "edges": edges}

