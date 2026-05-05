"use client";

import { useRef, useMemo, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";

// Descriptions shown when clicking a node
const AGENT_INFO: Record<string, string> = {
  intake: "Collects applicant info, runs eligibility check",
  docs: "Determines required documents, guides upload",
  verify: "Extracts data from documents via Azure AI",
  kyc: "PAN, Aadhaar verification and cross-check",
  cibil: "Pulls credit bureau reports (CIBIL, Experian)",
  income: "Verifies salary from bank statements & payslips",
  risk: "4Cs framework: Character, Capacity, Capital, Collateral",
  fraud: "Detects identity fraud and document tampering",
  score: "Combines all scores into composite 300-900",
  comply: "RBI compliance, fair lending, bias checks",
  price: "Interest rate, EMI, fees from rate card",
  decide: "Final decision: Approve / Deny / Escalate",
  offer: "Generates loan offer with EMI schedule",
};

// Tighter layout — fits within view without clipping
const AGENTS = [
  { id: "intake", label: "INTAKE", pos: [0, 2.2, 0] as [number, number, number], color: "#D4A853" },
  { id: "docs", label: "DOCS", pos: [-1.4, 1.3, 0.4] as [number, number, number], color: "#D4A853" },
  { id: "verify", label: "VERIFY", pos: [1.4, 1.3, -0.4] as [number, number, number], color: "#D4A853" },
  { id: "kyc", label: "KYC", pos: [-2.2, 0.3, 0.8] as [number, number, number], color: "#4FC3F7" },
  { id: "cibil", label: "CIBIL", pos: [0, 0.4, -0.8] as [number, number, number], color: "#4FC3F7" },
  { id: "income", label: "INCOME", pos: [2.2, 0.3, 0.4] as [number, number, number], color: "#4FC3F7" },
  { id: "risk", label: "RISK", pos: [-1.6, -0.6, 0] as [number, number, number], color: "#FF7043" },
  { id: "fraud", label: "FRAUD", pos: [1.6, -0.6, -0.4] as [number, number, number], color: "#FF7043" },
  { id: "score", label: "SCORE", pos: [0, -1.0, 0.4] as [number, number, number], color: "#66BB6A" },
  { id: "comply", label: "COMPLY", pos: [-1.3, -1.8, -0.3] as [number, number, number], color: "#AB47BC" },
  { id: "price", label: "PRICE", pos: [1.3, -1.8, 0.3] as [number, number, number], color: "#AB47BC" },
  { id: "decide", label: "DECIDE", pos: [0, -2.4, 0] as [number, number, number], color: "#D4A853" },
  { id: "offer", label: "OFFER", pos: [0, -3.0, 0] as [number, number, number], color: "#66BB6A" },
];

const EDGES: [string, string][] = [
  ["intake", "docs"], ["intake", "verify"],
  ["docs", "kyc"], ["verify", "cibil"], ["verify", "income"],
  ["kyc", "risk"], ["cibil", "risk"], ["income", "fraud"],
  ["risk", "score"], ["fraud", "score"],
  ["score", "comply"], ["score", "price"],
  ["comply", "decide"], ["price", "decide"],
  ["decide", "offer"],
];

function AgentNode({ position, id, label, color, isActive, onHover, onUnhover, onClick }: {
  position: [number, number, number];
  id: string;
  label: string;
  color: string;
  isActive: boolean;
  onHover: () => void;
  onUnhover: () => void;
  onClick: () => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const floatOffset = useMemo(() => Math.random() * Math.PI * 2, []);

  useFrame((state) => {
    const floatY = Math.sin(state.clock.elapsedTime * 1.5 + floatOffset) * 0.05;
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.008;
      meshRef.current.position.y = position[1] + floatY;
    }
    if (glowRef.current) {
      const s = isActive ? 1.6 : 1 + Math.sin(state.clock.elapsedTime * 2 + floatOffset) * 0.08;
      glowRef.current.scale.setScalar(s);
      glowRef.current.position.y = position[1] + floatY;
    }
  });

  return (
    <group>
      <mesh ref={glowRef} position={position}>
        <sphereGeometry args={[0.32, 16, 16]} />
        <meshBasicMaterial color={color} transparent opacity={isActive ? 0.25 : 0.06} />
      </mesh>

      <mesh
        ref={meshRef}
        position={position}
        onPointerOver={(e) => { e.stopPropagation(); onHover(); }}
        onPointerOut={onUnhover}
        onClick={(e) => { e.stopPropagation(); onClick(); }}
      >
        <dodecahedronGeometry args={[0.2, 0]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isActive ? 1.2 : 0.4}
          metalness={0.7}
          roughness={0.3}
          transparent
          opacity={0.9}
        />
      </mesh>

      <Html position={[position[0], position[1] - 0.4, position[2]]} center distanceFactor={8}>
        <div style={{
          color: isActive ? "#ffffff" : "rgba(255,255,255,0.55)",
          fontSize: "9px",
          fontFamily: "Inter, system-ui, sans-serif",
          fontWeight: 600,
          letterSpacing: "1.2px",
          whiteSpace: "nowrap",
          textShadow: "0 1px 6px rgba(0,0,0,0.9)",
          pointerEvents: "none",
          userSelect: "none",
          transition: "color 0.2s",
        }}>
          {label}
        </div>
      </Html>
    </group>
  );
}

function EdgeLine({ start, end, highlighted }: { start: [number, number, number]; end: [number, number, number]; highlighted: boolean }) {
  const { position, rotation, length } = useMemo(() => {
    const from = new THREE.Vector3(...start);
    const to = new THREE.Vector3(...end);
    const mid = from.clone().add(to).multiplyScalar(0.5);
    const direction = to.clone().sub(from);
    const len = direction.length();
    const q = new THREE.Quaternion();
    q.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
    const e = new THREE.Euler().setFromQuaternion(q);
    return {
      position: [mid.x, mid.y, mid.z] as [number, number, number],
      rotation: [e.x, e.y, e.z] as [number, number, number],
      length: len,
    };
  }, [start, end]);

  return (
    <mesh position={position} rotation={rotation}>
      <cylinderGeometry args={[highlighted ? 0.02 : 0.008, highlighted ? 0.02 : 0.008, length, 4]} />
      <meshBasicMaterial color={highlighted ? "#D4A853" : "#D4A853"} transparent opacity={highlighted ? 0.5 : 0.15} />
    </mesh>
  );
}

function DataParticle({ start, end, speed, delay }: {
  start: [number, number, number];
  end: [number, number, number];
  speed: number;
  delay: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    const t = ((state.clock.elapsedTime * speed + delay) % 3) / 3;
    const curve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(...start),
      new THREE.Vector3((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, (start[2] + end[2]) / 2 + 0.25),
      new THREE.Vector3(...end),
    );
    meshRef.current.position.copy(curve.getPoint(t));
    meshRef.current.scale.setScalar(0.6 + Math.sin(t * Math.PI) * 0.5);
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.035, 8, 8]} />
      <meshBasicMaterial color="#D4A853" transparent opacity={0.9} />
    </mesh>
  );
}

function Scene({ selectedNode, onSelectNode }: { selectedNode: string | null; onSelectNode: (id: string | null) => void }) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.1) * 0.18;
    }
  });

  const agentMap = useMemo(() => {
    const map: Record<string, (typeof AGENTS)[0]> = {};
    AGENTS.forEach((a) => { map[a.id] = a; });
    return map;
  }, []);

  const activeNode = selectedNode || hoveredNode;

  // Highlight edges connected to the active node
  const activeEdges = useMemo(() => {
    if (!activeNode) return new Set<number>();
    const set = new Set<number>();
    EDGES.forEach(([from, to], i) => {
      if (from === activeNode || to === activeNode) set.add(i);
    });
    return set;
  }, [activeNode]);

  return (
    <group ref={groupRef} position={[0, 0.5, 0]}>
      <ambientLight intensity={0.4} />
      <pointLight position={[5, 5, 5]} intensity={1} color="#D4A853" />
      <pointLight position={[-5, -3, 3]} intensity={0.5} color="#4FC3F7" />

      {EDGES.map(([from, to], i) => {
        const fa = agentMap[from];
        const ta = agentMap[to];
        if (!fa || !ta) return null;
        return (
          <group key={`e-${i}`}>
            <EdgeLine start={fa.pos} end={ta.pos} highlighted={activeEdges.has(i)} />
            <DataParticle start={fa.pos} end={ta.pos} speed={0.25 + i * 0.03} delay={i * 0.5} />
          </group>
        );
      })}

      {AGENTS.map((a) => (
        <AgentNode
          key={a.id}
          id={a.id}
          position={a.pos}
          label={a.label}
          color={a.color}
          isActive={activeNode === a.id}
          onHover={() => setHoveredNode(a.id)}
          onUnhover={() => setHoveredNode(null)}
          onClick={() => onSelectNode(selectedNode === a.id ? null : a.id)}
        />
      ))}
    </group>
  );
}

export function AgentGraph3D() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  return (
    <div className="w-full h-[500px] relative">
      <Canvas
        camera={{ position: [0, 0, 8.5], fov: 42 }}
        style={{ background: "transparent" }}
        gl={{ alpha: true, antialias: true }}
        onCreated={({ gl }) => { gl.setClearColor(0x000000, 0); }}
        onPointerMissed={() => setSelectedNode(null)}
      >
        <Scene selectedNode={selectedNode} onSelectNode={setSelectedNode} />
      </Canvas>

      {/* Info panel — shows on click */}
      {selectedNode && (
        <div className="absolute top-4 left-4 max-w-[220px] bg-[#0F172A]/90 backdrop-blur-md border border-[#D4A853]/30 rounded-xl p-4 shadow-2xl">
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: AGENTS.find((a) => a.id === selectedNode)?.color }}
            />
            <span className="text-white text-sm font-semibold tracking-wide">
              {AGENTS.find((a) => a.id === selectedNode)?.label}
            </span>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed">
            {AGENT_INFO[selectedNode]}
          </p>
        </div>
      )}
    </div>
  );
}
