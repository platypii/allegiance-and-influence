import { Edge } from "./forcegraph";

// Function to shuffle an array using Fisher-Yates algorithm
function shuffleArray(array: string[]): string[] {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

/**
 * Generates random edges ensuring each node is part of at most one connection.
 * @param nodes - An array of node names.
 * @param numberOfConnections - The number of desired unique connections.
 * @returns An array of Edge objects.
 * @throws Will throw an error if there aren't enough nodes to create the desired number of connections.
 */
export function randomEdges(nodes: string[], numberOfConnections: number): Edge[] {
  // Check if there are enough nodes to make the desired number of connections
  if (nodes.length < numberOfConnections * 2) {
    throw new Error(
      `Not enough nodes to make ${numberOfConnections} connections. Require at least ${
        numberOfConnections * 2
      } nodes, but got ${nodes.length}.`
    );
  }

  // Shuffle the nodes to ensure randomness
  const shuffledNodes = shuffleArray(nodes)

  const edges: Edge[] = []

  for (let i = 0; i < numberOfConnections; i++) {
    const source = shuffledNodes[2 * i]
    const target = shuffledNodes[2 * i + 1]
    edges.push({ source, target })
  }

  return edges;
}