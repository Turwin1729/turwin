import React, { useEffect, useCallback, useState } from 'react';
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
import VulnerabilityScanPage from './VulnerabilityScanPage';

const VisualizationContainer = styled.div`
  width: 100vw;
  height: 100vh;
  background: #1E2A38;
  opacity: ${props => props.visible ? 1 : 0};
  transition: opacity 0.5s ease-in-out;
`;

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(30, 42, 56, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  color: #E0E0E0;
  font-size: 24px;
  z-index: 1000;
`;

const HORIZONTAL_SPACING = 400;
const VERTICAL_SPACING = 200;

/** 
 * buildHierarchy: 
 * Takes the array of streamed nodes and reconstructs them into a tree structure
 */
function buildHierarchy(streamedNodes) {
  // Put them in a map by node_id
  const map = {};
  streamedNodes.forEach((n) => {
    // create a fresh copy; we'll replace "children" array of IDs with actual objects
    map[n.node_id] = { ...n, children: [...n.children] };
  });

  // Link children: replace each child's ID with the actual object
  Object.values(map).forEach((node) => {
    node.children = node.children.map((childId) => map[childId]).filter(Boolean);
  });

  // Find the root node
  let rootNode = Object.values(map).find((node) => node.type === 'root');
  if (!rootNode) {
    // fallback: find node that is not a child of anyone else
    const allChildren = new Set();
    Object.values(map).forEach((n) => {
      n.children.forEach((c) => allChildren.add(c.node_id));
    });
    const candidate = Object.keys(map).find((id) => !allChildren.has(id));
    rootNode = map[candidate];
  }

  return rootNode;
}

/** 
 * createTreeElements:
 * Takes a hierarchical node and creates a React Flow compatible layout
 */
function createTreeElements(rootNode) {
  const nodes = [];
  const edges = [];
  let nodeIndex = 0;

  function calculateSubtreeWidth(node) {
    if (!node.children || node.children.length === 0) {
      return 1;
    }
    return node.children.reduce((acc, child) => acc + calculateSubtreeWidth(child), 0);
  }

  function traverse(node, parentId = null, depth = 0, xOffset = 0) {
    const thisId = `node-${nodeIndex++}`;
    const subtreeWidth = calculateSubtreeWidth(node);
    const x = xOffset * HORIZONTAL_SPACING;
    const y = depth * VERTICAL_SPACING;

    nodes.push({
      id: thisId,
      position: { x, y },
      data: {
        label: node.method 
          ? `${node.title} (${node.method})`
          : node.title,
      },
      style: {
        background: node.type === 'root' ? '#1a2634' : '#16202C',
        color: '#E0E0E0',
        border: '2px solid #00ADB5',
        padding: '15px',
        borderRadius: '8px',
        minWidth: '180px',
        fontSize: node.type === 'root' ? '16px' : '14px',
        fontWeight: node.type === 'root' ? 'bold' : 'normal',
        textAlign: 'center',
      },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
    });

    if (parentId) {
      edges.push({
        id: `edge-${parentId}-${thisId}`,
        source: parentId,
        target: thisId,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#00ADB5', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#00ADB5'
        }
      });
    }

    if (node.children && node.children.length > 0) {
      let currentOffset = xOffset - (subtreeWidth / 2);
      node.children.forEach((child) => {
        const childWidth = calculateSubtreeWidth(child);
        currentOffset += childWidth / 2;
        traverse(child, thisId, depth + 1, currentOffset);
        currentOffset += childWidth / 2;
      });
    }
  }

  if (!rootNode) {
    return { nodes: [], edges: [] };
  }

  traverse(rootNode, null, 0, 0);
  return { nodes, edges };
}

const VisualizationPage = () => {
  // Store raw streamed nodes
  const [streamedNodes, setStreamedNodes] = useState([]);
  const [isSocketOpen, setIsSocketOpen] = useState(false);
  const [isSocketClosed, setIsSocketClosed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // ReactFlow states
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [showPage3, setShowPage3] = useState(false);
  const [page2Visible, setPage2Visible] = useState(true);

  // WebSocket connection and handling
  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws");

    socket.onopen = () => {
      console.log("WebSocket connected!");
      setIsSocketOpen(true);
      setIsLoading(true);
      
      // Once connected, tell the server to start streaming
      fetch("http://localhost:8000/start-stream")
        .then(res => {
          if (!res.ok) throw new Error("Failed to start streaming");
          return res.json();
        })
        .then(data => {
          console.log("Streaming started:", data);
        })
        .catch(err => {
          console.error("Error starting stream:", err);
          setError("Failed to start streaming");
          setIsLoading(false);
        });
    };

    socket.onmessage = (event) => {
      try {
        const node = JSON.parse(event.data);
        console.log("Received node:", node);

        // Add the new node to our list
        setStreamedNodes(prev => {
          const updatedNodes = [...prev, node];
          
          // Build the hierarchy and update visualization
          const root = buildHierarchy(updatedNodes);
          const { nodes: newNodes, edges: newEdges } = createTreeElements(root);
          
          setNodes(newNodes);
          setEdges(newEdges);
          setIsLoading(false);
          
          return updatedNodes;
        });

      } catch (err) {
        console.error("Error parsing WebSocket message:", err);
      }
    };

    socket.onclose = () => {
      console.log("WebSocket closed");
      setIsSocketOpen(false);
      setIsSocketClosed(true);
      setIsLoading(false);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
      setError("WebSocket error occurred");
      setIsSocketOpen(false);
      setIsSocketClosed(true);
      setIsLoading(false);
    };

    // Cleanup on unmount
    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, []);

  const onInit = useCallback((reactFlowInstance) => {
    console.log('React Flow initialized');
    reactFlowInstance.fitView({ padding: 0.2 });

    // Transition to Page 3 after 2 seconds
    setTimeout(() => {
      setPage2Visible(false);
      setTimeout(() => {
        setShowPage3(true);
      }, 500); // Wait for fade-out before showing Page 3
    }, 2000);
  }, []);

  if (error) {
    return (
      <VisualizationContainer>
        <LoadingOverlay>{error}</LoadingOverlay>
      </VisualizationContainer>
    );
  }

  return (
    <>
      <VisualizationContainer visible={page2Visible}>
        {isLoading && !error && (
          <LoadingOverlay>
            Loading visualization...
          </LoadingOverlay>
        )}
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
          style={{ opacity: isLoading ? 0.4 : 1 }}
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
      {showPage3 && (
        <VulnerabilityScanPage
          treeData={{ nodes, edges }}
          visible={showPage3}
        />
      )}
    </>
  );
};

export default VisualizationPage;
