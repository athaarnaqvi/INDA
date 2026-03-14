"""
Topology Image Generation Module for GNS3 INDA
Generates SVG and XML visualizations of network topologies before deployment
Location: VisioGns3/topology_visualization.py
"""

import json
import os
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math
from datetime import datetime


@dataclass
class Node:
    """Represents a network node (device)"""
    name: str
    node_type: str
    x: float
    y: float
    symbol: str
    template_id: str
    properties: Dict = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class Connection:
    """Represents a link between two nodes"""
    from_node: str
    to_node: str
    from_adapter: int = 0
    from_port: int = 0
    to_adapter: int = 0
    to_port: int = 0



# Add this new class before TopologyParser

class ConnectionMapper:
    """Maps connection names to actual device names"""
    
    @staticmethod
    def fuzzy_match_device(device_name: str, available_devices: Dict[str, Node]) -> Optional[str]:
        """
        Find the closest matching device name if exact match doesn't exist.
        E.g., 'pc_f1_r1_u1' -> 'laptop_f1_r1_u1'
        """
        if device_name in available_devices:
            return device_name
        
        # Try variations
        variations = [
            device_name.replace('pc_', 'laptop_'),
            device_name.replace('laptop_', 'pc_'),
            device_name.replace('pc', 'laptop'),
            device_name.replace('laptop', 'pc'),
        ]
        
        for variant in variations:
            if variant in available_devices:
                print(f"      🔄 Mapped '{device_name}' → '{variant}'")
                return variant
        
        # Try substring matching
        for available in available_devices.keys():
            # Extract parts and compare
            device_parts = device_name.split('_')
            available_parts = available.split('_')
            
            # If they match except for pc/laptop prefix
            if len(device_parts) > 1 and len(available_parts) > 1:
                if device_parts[1:] == available_parts[1:]:
                    print(f"      🔄 Mapped '{device_name}' → '{available}' (by suffix match)")
                    return available
        
        return None


class TopologyParser:
    """Parses YAML machine and connection data into topology objects"""
    
    def __init__(self, machines_yaml_path: str, connections_json_path: str):
        self.machines_yaml_path = machines_yaml_path
        self.connections_json_path = connections_json_path
        self.nodes: Dict[str, Node] = {}
        self.connections: List[Connection] = []
    
    def parse_yaml_machines(self) -> Dict[str, Node]:
        """
        Parse Gns3_Machines.yaml to extract node information
        Expected format from ansible playbook
        """
        # Clear previous nodes
        self.nodes.clear()
        
        try:
            import yaml
        except ImportError:
            print("[WARNING] PyYAML not installed, using manual parsing")
            return self._parse_yaml_manual()
        
        try:
            with open(self.machines_yaml_path, 'r') as f:
                playbook = yaml.safe_load(f)
            
            if not playbook or not isinstance(playbook, list):
                print(f"[WARNING] Invalid YAML format: {type(playbook)}")
                return {}
            
            # Extract nodes from Ansible playbook tasks
            for task in playbook[0].get('tasks', [])[1:]:  # Skip project creation task
                if not isinstance(task, dict):
                    continue
                
                body = task.get('uri', {}).get('body', '{}')
                
                # Handle both string and dict body
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except:
                        continue
                
                if isinstance(body, dict) and 'name' in body:
                    node = Node(
                        name=body['name'],
                        node_type=body.get('node_type', 'unknown'),
                        x=float(body.get('x', 0)),
                        y=float(body.get('y', 0)),
                        symbol=body.get('symbol', ''),
                        template_id=body.get('template_id', ''),
                        properties=body.get('properties', {})
                    )
                    self.nodes[node.name] = node
                    print(f"    📍 {node.name}")
            
            print(f"  ✅ Parsed {len(self.nodes)} devices from YAML")
            return self.nodes
        
        except Exception as e:
            print(f"  [ERROR] Failed to parse machines YAML: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _parse_yaml_manual(self) -> Dict[str, Node]:
        """Manual YAML parsing without PyYAML"""
        try:
            with open(self.machines_yaml_path, 'r') as f:
                content = f.read()
            
            # Extract device blocks from YAML
            import re
            device_pattern = r'- name: Add (\w+).*?"name":\s*"([^"]+)".*?"x":\s*(\d+).*?"y":\s*(\d+).*?"node_type":\s*"([^"]+)"'
            
            for match in re.finditer(device_pattern, content, re.DOTALL):
                device_name = match.group(2)
                node = Node(
                    name=device_name,
                    node_type=match.group(5),
                    x=float(match.group(3)),
                    y=float(match.group(4)),
                    symbol='',
                    template_id=''
                )
                self.nodes[device_name] = node
            
            print(f"  ✅ Parsed {len(self.nodes)} devices from YAML (manual)")
            return self.nodes
        except Exception as e:
            print(f"  [ERROR] Manual YAML parsing failed: {e}")
            return {}
    
    def parse_json_connections(self) -> List[Connection]:
        """
        Parse Connections.json to extract link information
        Expected format: {"from": "device1", "to": "device2", ...}
        """
        # Clear previous connections
        self.connections.clear()
        
        try:
            with open(self.connections_json_path, 'r') as f:
                connections_data = json.load(f)
            
            if not isinstance(connections_data, list):
                print(f"  [WARNING] Connections data is not a list: {type(connections_data)}")
                return []
            
            print(f"  📄 JSON file contains {len(connections_data)} entries")
            print(f"  📍 Available devices: {', '.join(sorted(self.nodes.keys()))}\n")
            
            valid_connections = 0
            for i, conn in enumerate(connections_data):
                if not isinstance(conn, dict):
                    print(f"    [SKIP {i}] Not a dict: {type(conn)}")
                    continue
                
                from_node = conn.get('from', '')
                to_node = conn.get('to', '')
                from_adapter = conn.get('from_adapter_number', 0)
                from_port = conn.get('from_port_number', 0)
                to_adapter = conn.get('to_adapter_number', 0)
                to_port = conn.get('to_port_number', 0)
                
                if not from_node or not to_node:
                    print(f"    [SKIP {i}] Missing from/to: {conn}")
                    continue
                
                # Try to find matching devices (with fuzzy matching)
                actual_from = ConnectionMapper.fuzzy_match_device(from_node, self.nodes)
                actual_to = ConnectionMapper.fuzzy_match_device(to_node, self.nodes)
                
                if not actual_from:
                    print(f"    [SKIP {i}] ❌ Source '{from_node}' NOT found (tried: {from_node}, pc_*, laptop_*)")
                    continue
                
                if not actual_to:
                    print(f"    [SKIP {i}] ❌ Target '{to_node}' NOT found (tried: {to_node}, pc_*, laptop_*)")
                    continue
                
                connection = Connection(
                    from_node=actual_from,
                    to_node=actual_to,
                    from_adapter=from_adapter,
                    from_port=from_port,
                    to_adapter=to_adapter,
                    to_port=to_port
                )
                self.connections.append(connection)
                valid_connections += 1
                print(f"    ✅ [{valid_connections}] {actual_from} → {actual_to} (port {from_adapter}.{from_port} → {to_adapter}.{to_port})")
            
            print(f"\n  ✅ Parsed {valid_connections}/{len(connections_data)} valid connections from JSON")
            return self.connections
        
        except Exception as e:
            print(f"  [ERROR] Failed to parse connections JSON: {e}")
            import traceback
            traceback.print_exc()
            return []


# Replace the LayoutCalculator class with this:

class LayoutCalculator:
    """Calculates hierarchical layout for nodes based on network topology"""
    
    @staticmethod
    def calculate_layout(nodes: Dict[str, Node], connections: List[Connection]) -> Dict[str, Tuple[float, float]]:

        import re

        layout = {}

        # spacing
        floor_spacing = 220
        node_spacing = 160

        # separate core devices
        core_nodes = []
        floor_nodes = {}

        for node_name, node in nodes.items():

            name = node_name.lower()

            # detect core devices
            if (
                "core" in name
                or "router" in name
                or "firewall" in name
                or "internet" in name
                or node.node_type in ["router", "cloud", "firewall"]
            ):
                core_nodes.append(node_name)
                continue

            # detect floor number
            match = re.search(r"_f(\d+)", name)

            if match:
                floor = int(match.group(1))
            else:
                floor = 0

            floor_nodes.setdefault(floor, []).append(node_name)

        y = 120

        # -------------------
        # CORE LAYER
        # -------------------
        if core_nodes:

            start_x = 400
            for i, node in enumerate(sorted(core_nodes)):
                layout[node] = (start_x + i * node_spacing, y)

            print(f"  📍 Core Layer: {core_nodes}")

            y += floor_spacing

        # -------------------
        # FLOOR LAYERS
        # -------------------
        for floor in sorted(floor_nodes.keys()):

            devices = sorted(floor_nodes[floor])

            # classify devices
            dist_switches = []
            access_points = []
            access_switches = []
            pcs = []

            for dev in devices:
                name = dev.lower()

                if "dist" in name:
                    dist_switches.append(dev)
                elif "ap" in name or "access_point" in name:
                    access_points.append(dev)
                elif "switch" in name:
                    access_switches.append(dev)
                elif "pc" in name or "laptop" in name or "host" in name:
                    pcs.append(dev)
                else:
                    pcs.append(dev)

            print(f"  🏢 Floor {floor}")
            print(f"     Dist: {dist_switches}")
            print(f"     APs : {access_points}")
            print(f"     SW  : {access_switches}")
            print(f"     PCs : {pcs}")

            # Distribution switches and APs should be on the same horizontal layer
            distribution_layer = dist_switches + access_points

            layer_groups = [
                distribution_layer,
                access_switches,
                pcs
            ]

            layer_y = y

            for layer in layer_groups:

                if not layer:
                    continue

                total_width = (len(layer) - 1) * node_spacing
                start_x = max(200, (1200 - total_width) / 2)

                for i, node in enumerate(layer):
                    layout[node] = (start_x + i * node_spacing, layer_y)

                layer_y += 120

            y = layer_y + 100

        return layout
    
    @staticmethod
    def _identify_layers(nodes: Dict[str, Node], adjacency: Dict) -> List[Tuple[str, List[str]]]:
        """
        Identify network layers based on device types and connectivity.
        Returns list of (layer_name, [nodes_in_layer])
        """
        layers = []
        assigned = set()
        
        # Layer 1: Core devices (routers, cloud)
        core_layer = []
        for node_name, node in nodes.items():
            if node.node_type in ['router', 'cloud', 'firewall'] or 'core' in node_name.lower() or 'internet' in node_name.lower():
                core_layer.append(node_name)
                assigned.add(node_name)
        if core_layer:
            layers.append(("Core/Internet", core_layer))
        
        # Layer 2: Distribution switches
        dist_layer = []
        for node_name, node in nodes.items():
            if node_name not in assigned:
                if 'dist_switch' in node_name.lower() or (node.node_type == 'ethernet_switch' and 'dist' in node_name.lower()):
                    dist_layer.append(node_name)
                    assigned.add(node_name)
        if dist_layer:
            layers.append(("Distribution", dist_layer))
        
        # Layer 3: Access switches and servers
        access_layer = []
        for node_name, node in nodes.items():
            if node_name not in assigned:
                if node.node_type == 'ethernet_switch' or 'switch' in node_name.lower() or node.node_type == 'qemu':
                    access_layer.append(node_name)
                    assigned.add(node_name)
        if access_layer:
            layers.append(("Access/Servers", access_layer))
        
        # Layer 4: End devices (PCs, etc.)
        device_layer = []
        for node_name, node in nodes.items():
            if node_name not in assigned:
                device_layer.append(node_name)
                assigned.add(node_name)
        if device_layer:
            layers.append(("End Devices", device_layer))
        
        return layers

class SVGGenerator:
    """Generates SVG visualization of the network topology"""
    
    # Device type to icon/symbol mapping
    DEVICE_COLORS = {
        'ethernet_switch': '#87CEEB',
        'qemu': '#FFB6C1',
        'router': '#98FB98',
        'cloud': '#FFE4B5',
        'nat': '#DDA0DD',
        'vpcs': '#F0E68C',
        'firewall': '#FF6347',
        'hub': '#DEB887',
    }
    
    DEVICE_ICONS = {
        'ethernet_switch': '🔀',
        'qemu': '💻',
        'router': '🔀',
        'cloud': '☁️',
        'nat': '🔄',
        'vpcs': '🖥️',
        'firewall': '🛡️',
        'hub': '⚡',
    }
    
    def __init__(self, nodes: Dict[str, Node], connections: List[Connection], 
                 title: str = "Network Topology", auto_layout: bool = True):
        self.nodes = nodes
        self.connections = connections
        self.title = title
        self.padding = 100
        self.node_width = 120
        self.node_height = 85
        self.font_size = 11
        
        # Apply automatic layout if requested
        if auto_layout:
            self._apply_auto_layout()
    
    def _apply_auto_layout(self):
        """Apply automatic hierarchical layout to nodes"""
        print("  📐 Calculating hierarchical node positions...")
        layout = LayoutCalculator.calculate_layout(self.nodes, self.connections)
        
        # Update node positions
        positioned = 0
        for node_name, (x, y) in layout.items():
            if node_name in self.nodes:
                self.nodes[node_name].x = x
                self.nodes[node_name].y = y
                positioned += 1
        
        print(f"  ✅ Layout calculated and applied to {positioned}/{len(self.nodes)} nodes")
    
    def _calculate_dimensions(self) -> Tuple[int, int]:
        """Calculate SVG dimensions based on node positions"""
        if not self.nodes:
            return 1200, 800
        
        max_x = max((node.x for node in self.nodes.values()), default=0) + self.node_width
        max_y = max((node.y for node in self.nodes.values()), default=0) + self.node_height
        
        width = max(1200, int(max_x) + self.padding * 2)
        height = max(800, int(max_y) + self.padding * 2)
        
        return width, height
    
    def _get_device_color(self, node_type: str) -> str:
        """Get color for device type"""
        for key, color in self.DEVICE_COLORS.items():
            if key in node_type.lower():
                return color
        return '#CCCCCC'
    
    def _get_device_icon(self, node_type: str) -> str:
        """Get icon for device type"""
        for key, icon in self.DEVICE_ICONS.items():
            if key in node_type.lower():
                return icon
        return '◊'
    
    def _create_node_svg(self, node: Node, x_offset: int, y_offset: int) -> str:
        """Create SVG representation of a single node"""
        x = node.x + x_offset
        y = node.y + y_offset
        color = self._get_device_color(node.node_type)
        icon = self._get_device_icon(node.node_type)
        
        # Truncate long names
        display_name = node.name if len(node.name) <= 16 else node.name[:13] + "..."
        
        svg = f'''
    <!-- Node: {node.name} -->
    <g id="node-{node.name.replace('_', '-')}" class="device">
        <!-- Device box -->
        <rect x="{x}" y="{y}" width="{self.node_width}" height="{self.node_height}" 
              fill="{color}" stroke="#333333" stroke-width="2.5" rx="6" ry="6" />
        
        <!-- Device icon -->
        <text x="{x + self.node_width/2}" y="{y + 18}" 
              text-anchor="middle" font-size="20" dominant-baseline="middle">{icon}</text>
        
        <!-- Device name -->
        <text x="{x + self.node_width/2}" y="{y + 50}" 
              text-anchor="middle" font-size="{self.font_size}" font-weight="bold"
              fill="#000000" dominant-baseline="middle">{display_name}</text>
        
        <!-- Device type -->
        <text x="{x + self.node_width/2}" y="{y + 68}" 
              text-anchor="middle" font-size="8" fill="#555555" dominant-baseline="middle">{node.node_type}</text>
        
        <!-- Hover tooltip -->
        <title>{node.name} ({node.node_type})</title>
    </g>
'''
        return svg
    
    def _create_connection_svg(self, conn: Connection, x_offset: int, y_offset: int) -> str:
        """Create SVG representation of a connection with better visibility"""
        from_node = self.nodes.get(conn.from_node)
        to_node = self.nodes.get(conn.to_node)
        
        if not from_node or not to_node:
            return ''
        
        # Calculate center points of nodes
        from_x = from_node.x + self.node_width / 2 + x_offset
        from_y = from_node.y + self.node_height / 2 + y_offset
        to_x = to_node.x + self.node_width / 2 + x_offset
        to_y = to_node.y + self.node_height / 2 + y_offset
        
        # Calculate distance
        dx = to_x - from_x
        dy = to_y - from_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:  # Changed from == 0 to < 1 for better handling
            return ''
        
        # Use quadratic bezier for curves
        offset = min(distance * 0.15, 80)  # Cap the curve offset
        ctrl_x = (from_x + to_x) / 2 + offset * (-dy / distance)
        ctrl_y = (from_y + to_y) / 2 + offset * (dx / distance)
        
        # Label position
        label_x = (from_x + to_x) / 2
        label_y = (from_y + to_y) / 2 - 15
        
        try:
            svg = f'''
    <!-- Connection: {conn.from_node} → {conn.to_node} -->
    <g class="connection" id="conn-{conn.from_node.replace('_', '-')}-to-{conn.to_node.replace('_', '-')}">
        <!-- Connection line -->
        <path d="M {from_x} {from_y} Q {ctrl_x} {ctrl_y} {to_x} {to_y}"
              stroke="#666666" stroke-width="2" fill="none" 
              marker-end="url(#arrowhead)" stroke-linecap="round" stroke-linejoin="round" />
        
        <!-- Port label -->
        <rect x="{label_x - 50}" y="{label_y - 12}" width="100" height="20" 
              fill="white" stroke="#999" stroke-width="1" rx="3" opacity="0.95" />
        <text x="{label_x}" y="{label_y + 2}" 
              text-anchor="middle" font-size="8" fill="#333333" font-weight="bold"
              dominant-baseline="middle">
            {conn.from_adapter}.{conn.from_port}→{conn.to_adapter}.{conn.to_port}
        </text>
    </g>
'''
            return svg
        except Exception as e:
            print(f"      ❌ Exception creating SVG: {e}")
            return ''
    
# Find the generate() method in SVGGenerator class and replace it with this:

    def generate(self) -> str:
        """Generate complete SVG document"""
        width, height = self._calculate_dimensions()
        x_offset = self.padding
        y_offset = self.padding
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"  📐 SVG: {width}x{height} | 📍 Nodes: {len(self.nodes)} | 🔗 Connections: {len(self.connections)}")
        
        # Generate SVG with viewBox for responsiveness
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {width} {height}"
     version="1.1"
     preserveAspectRatio="xMidYMid meet"
     style="width:100%; height:auto; border:1px solid #ddd;">
    
    <defs>
        <!-- Arrow marker -->
        <marker id="arrowhead" markerWidth="13" markerHeight="13" 
                refX="12" refY="6" orient="auto">
            <polygon points="0 0, 13 6, 0 12" fill="#666666" />
        </marker>
        
        <!-- Styles -->
        <style>
            .device {{ cursor: pointer; }}
            .device:hover {{ opacity: 0.9; filter: drop-shadow(0 0 4px rgba(0,0,0,0.3)); }}
            .connection {{ pointer-events: none; }}
            text {{ font-family: Arial, Helvetica, sans-serif; }}
        </style>
    </defs>
    
    <!-- Background -->
    <rect width="{width}" height="{height}" fill="#FFFFFF" stroke="#E0E0E0" stroke-width="1" />
    
    <!-- Grid -->
    <defs>
        <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
            <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#F5F5F5" stroke-width="0.5"/>
        </pattern>
    </defs>
    <rect width="{width}" height="{height}" fill="url(#grid)" />
    
    <!-- Title -->
    <text x="{width/2}" y="35" text-anchor="middle" font-size="28" font-weight="bold" fill="#222">
        {self.title}
    </text>
    <text x="{width/2}" y="58" text-anchor="middle" font-size="11" fill="#999">
        {timestamp} | Devices: {len(self.nodes)} | Links: {len(self.connections)}
    </text>
    
    <!-- Connections -->
    <g id="connections">
'''
        
        if self.connections:
            print(f"  🔗 Rendering {len(self.connections)} connections:")
            rendered_count = 0
            for i, conn in enumerate(self.connections, 1):
                try:
                    svg_conn = self._create_connection_svg(conn, x_offset, y_offset)
                    if svg_conn and len(svg_conn.strip()) > 0:
                        print(f"    [{i}] ✅ {conn.from_node} → {conn.to_node}")
                        svg += svg_conn
                        rendered_count += 1
                    else:
                        print(f"    [{i}] ⚠️  EMPTY: {conn.from_node} → {conn.to_node}")
                except Exception as e:
                    print(f"    [{i}] ❌ ERROR: {conn.from_node} → {conn.to_node}: {str(e)}")
            print(f"  ✅ Successfully rendered {rendered_count}/{len(self.connections)} connections\n")
        else:
            print(f"  ⚠️  No connections to render!")
        
        svg += '''
    </g>
    
    <!-- Nodes -->
    <g id="nodes">
'''
        
        for node in self.nodes.values():
            svg += self._create_node_svg(node, x_offset, y_offset)
        
        svg += '''
    </g>
    
    <!-- Legend -->
    <g id="legend">
        <rect x="20" y="80" width="180" height="220" fill="#F9F9F9" 
              stroke="#AAA" stroke-width="1.5" rx="4" opacity="0.96" />
        <text x="110" y="102" text-anchor="middle" font-weight="bold" font-size="12" fill="#333">
            Device Types
        </text>
'''
        
        legend_y = 125
        for device_type, color in list(self.DEVICE_COLORS.items())[:9]:
            svg += f'''
        <rect x="30" y="{legend_y - 9}" width="13" height="13" 
              fill="{color}" stroke="#333" stroke-width="1" rx="2" />
        <text x="50" y="{legend_y - 2}" font-size="10" fill="#333">{device_type}</text>
'''
            legend_y += 20
        
        svg += '''
    </g>

</svg>
'''
        return svg


class XMLGenerator:
    """Generates XML representation of the network topology"""
    
    def __init__(self, nodes: Dict[str, Node], connections: List[Connection],
                 project_name: str = "topology"):
        self.nodes = nodes
        self.connections = connections
        self.project_name = project_name
    
    def generate(self) -> str:
        """Generate complete XML document"""
        timestamp = datetime.now().isoformat()
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<topology>
    <metadata>
        <name>{self.project_name}</name>
        <timestamp>{timestamp}</timestamp>
        <device_count>{len(self.nodes)}</device_count>
        <connection_count>{len(self.connections)}</connection_count>
    </metadata>
    
    <devices>
'''
        
        for node in self.nodes.values():
            properties_xml = ''
            if node.properties:
                for key, value in node.properties.items():
                    properties_xml += f'        <property name="{self._escape_xml(str(key))}">{self._escape_xml(str(value))}</property>\n'
            
            xml += f'''    <device>
        <name>{self._escape_xml(node.name)}</name>
        <type>{self._escape_xml(node.node_type)}</type>
        <position>
            <x>{node.x}</x>
            <y>{node.y}</y>
        </position>
        <symbol>{self._escape_xml(node.symbol)}</symbol>
        <template_id>{node.template_id}</template_id>
{properties_xml}    </device>
'''
        
        xml += '''    </connections>
    
    <statistics>
        <total_devices>{}</total_devices>
        <total_connections>{}</total_connections>
        <device_types>
'''.format(len(self.nodes), len(self.connections))
        
        if self.connections:
            print(f"  🔗 Writing {len(self.connections)} connections to XML:")
            xml_connections = '''    </devices>
    
    <connections>
'''
            for i, conn in enumerate(self.connections, 1):
                print(f"    [{i}] {conn.from_node} → {conn.to_node}")
                xml_connections += f'''    <connection>
        <from>
            <node>{self._escape_xml(conn.from_node)}</node>
            <adapter>{conn.from_adapter}</adapter>
            <port>{conn.from_port}</port>
        </from>
        <to>
            <node>{self._escape_xml(conn.to_node)}</node>
            <adapter>{conn.to_adapter}</adapter>
            <port>{conn.to_port}</port>
        </to>
    </connection>
'''
            xml = xml.replace('    </connections>', xml_connections)
        else:
            xml = xml.replace('    </connections>', '''    </devices>
    
    <connections>
''')
        
        device_types = {}
        for node in self.nodes.values():
            device_types[node.node_type] = device_types.get(node.node_type, 0) + 1
        
        for dtype, count in device_types.items():
            xml += f'        <type name="{self._escape_xml(dtype)}" count="{count}" />\n'
        
        xml += '''        </device_types>
    </statistics>
    
</topology>
'''
        return xml
    
    @staticmethod
    def _escape_xml(text: str) -> str:
        """Escape special XML characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))


class TopologyVisualizer:
    """Main class to coordinate topology visualization"""
    
    def __init__(self, machines_yaml_path: str, connections_json_path: str,
                 output_dir: str = "./topology_previews"):
        self.machines_yaml_path = machines_yaml_path
        self.connections_json_path = connections_json_path
        self.parser = TopologyParser(machines_yaml_path, connections_json_path)
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_svg(self, output_filename: Optional[str] = None) -> str:
        """Generate and save SVG visualization"""
        print("\n🎨 Generating SVG visualization...")
        
        # Parse topology data (fresh parse, clears previous data)
        self.parser.parse_yaml_machines()
        self.parser.parse_json_connections()
        
        # Generate SVG with auto layout
        svg_gen = SVGGenerator(
            self.parser.nodes, 
            self.parser.connections,
            auto_layout=True
        )
        svg_content = svg_gen.generate()
        
        # Save to file
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"topology_{timestamp}.svg"
        
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w') as f:
            f.write(svg_content)
        
        print(f"  ✅ SVG saved: {output_path}")
        return output_path
    
    def generate_xml(self, output_filename: Optional[str] = None) -> str:
        """Generate and save XML representation"""
        print("\n📋 Generating XML representation...")
        
        # Parse topology data (fresh parse, clears previous data)
        self.parser.parse_yaml_machines()
        self.parser.parse_json_connections()
        
        # Generate XML
        xml_gen = XMLGenerator(self.parser.nodes, self.parser.connections)
        xml_content = xml_gen.generate()
        
        # Save to file
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"topology_{timestamp}.xml"
        
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w') as f:
            f.write(xml_content)
        
        print(f"  ✅ XML saved: {output_path}")
        return output_path
    
    def generate_both(self) -> Tuple[str, str]:
        """Generate both SVG and XML visualizations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        svg_path = self.generate_svg(f"topology_{timestamp}.svg")
        xml_path = self.generate_xml(f"topology_{timestamp}.xml")
        
        return svg_path, xml_path
    
    def get_topology_summary(self) -> Dict:
        """Get summary statistics of the topology"""
        # Fresh parse to ensure correct counts
        self.parser.parse_yaml_machines()
        self.parser.parse_json_connections()
        
        device_types = {}
        for node in self.parser.nodes.values():
            device_types[node.node_type] = device_types.get(node.node_type, 0) + 1
        
        return {
            'total_devices': len(self.parser.nodes),
            'total_connections': len(self.parser.connections),
            'device_types': device_types,
            'devices': list(self.parser.nodes.keys()),
            'connections': [
                {
                    'from': c.from_node,
                    'to': c.to_node,
                    'from_port': f"{c.from_adapter}.{c.from_port}",
                    'to_port': f"{c.to_adapter}.{c.to_port}"
                }
                for c in self.parser.connections
            ]
        }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python topology_visualization.py <machines_yaml> <connections_json> [format]")
        print("  format: svg (default), xml, or both")
        sys.exit(1)
    
    machines_yaml = sys.argv[1]
    connections_json = sys.argv[2]
    format_type = sys.argv[3] if len(sys.argv) > 3 else 'svg'
    
    visualizer = TopologyVisualizer(machines_yaml, connections_json)
    
    if format_type.lower() == 'both':
        svg_path, xml_path = visualizer.generate_both()
    elif format_type.lower() == 'svg':
        visualizer.generate_svg()
    else:
        visualizer.generate_xml()
    
    summary = visualizer.get_topology_summary()
    print(f"\n📊 Topology Summary:")
    print(f"  Total Devices: {summary['total_devices']}")
    print(f"  Total Connections: {summary['total_connections']}")
    print(f"  Device Types: {summary['device_types']}")