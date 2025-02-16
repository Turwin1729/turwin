import React, { useEffect, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Position,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import styled from 'styled-components';
import fakeData from '../fake_parsed1.json';

const VisualizationContainer = styled.div`
  width: 100vw;
  height: 100vh;
  background: #1E2A38;
`;

const NODE_WIDTH = 200;
const NODE_HEIGHT = 100;
const HORIZONTAL_SPACING = 400;
const VERTICAL_SPACING = 200;

const createTreeElements = (data) => {
  const nodes = [];
  const edges = [];
  let nodeId = 1;

  // Calculate total width needed for a node and its children
  const calculateNodeWidth = (node) => {
    if (!node.children || node.children.length === 0) {
      return 1;
    }
    return node.children.reduce((sum, child) => sum + calculateNodeWidth(child), 0);
  };

  const processNode = (node, parentId = null, depth = 0, xOffset = 0) => {
    const id = `node-${nodeId++}`;

    // Calculate position
    const nodeWidth = calculateNodeWidth(node);
    const x = xOffset * HORIZONTAL_SPACING;
    const y = depth * VERTICAL_SPACING;

    const newNode = {
      id,
      type: 'default',
      position: { x, y },
      data: {
        label: `${node.name}${node.method ? ` (${node.method})` : ''}`,
        type: node.type,
      },
      style: {
        background: node.type === 'root' ? '#1a2634' : '#16202C',
        color: '#E0E0E0',
        border: `2px solid ${node.type === 'api' ? '#4CAF50' : '#00ADB5'}`,
        padding: '15px',
        borderRadius: '8px',
        minWidth: '180px',
        fontSize: node.type === 'root' ? '16px' : '14px',
        fontWeight: node.type === 'root' ? 'bold' : 'normal',
        boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
        textAlign: 'center'
      },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
      draggable: false,
    };

    nodes.push(newNode);
    console.log('Added node:', {
      id: newNode.id,
      label: newNode.data.label,
      position: newNode.position,
      type: node.type
    });

    if (parentId) {
      const newEdge = {
        id: `edge-${parentId}-${id}`,
        source: parentId,
        target: id,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#00ADB5', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#00ADB5',
        },
      };
      edges.push(newEdge);
      console.log('Added edge:', newEdge);
    }

    if (node.children) {
      let currentOffset = xOffset - (nodeWidth / 2);
      node.children.forEach((child) => {
        const childWidth = calculateNodeWidth(child);
        currentOffset += childWidth / 2;
        processNode(child, id, depth + 1, currentOffset);
        currentOffset += childWidth / 2;
      });
    }
  };

  processNode(data, null, 0, 0);
  return { nodes, edges };
};

const VisualizationPage = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onInit = useCallback((reactFlowInstance) => {
    console.log('React Flow initialized with:', {
      nodes: reactFlowInstance.getNodes(),
      edges: reactFlowInstance.getEdges()
    });

    // Force a re-render and fit view
    setTimeout(() => {
      reactFlowInstance.fitView({ padding: 0.2 });
      console.log('Fit view applied');
    }, 100);
  }, []);

  useEffect(() => {
    const { nodes: initialNodes, edges: initialEdges } = createTreeElements(fakeData);
    console.log('Setting initial tree data:', {
      nodeCount: initialNodes.length,
      nodes: initialNodes.map(n => ({ id: n.id, label: n.data.label })),
      edgeCount: initialEdges.length,
      edges: initialEdges.map(e => ({ id: e.id, source: e.source, target: e.target }))
    });
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, []);

  return (
    <VisualizationContainer>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onInit={onInit}
        fitView
        fitViewOptions={{
          padding: 0.2,
          includeHiddenNodes: true,
          minZoom: 0.5,
          maxZoom: 1.5
        }}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: true,
          style: { strokeWidth: 2 }
        }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={() => '#00ADB5'}
          maskColor="rgba(0, 0, 0, 0.2)"
          backgroundColor="#1E2A38"
        />
      </ReactFlow>
    </VisualizationContainer>
  );
};

export default VisualizationPage;
