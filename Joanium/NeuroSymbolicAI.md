---
name: Neuro-Symbolic AI
trigger: neuro-symbolic, neural symbolic, knowledge graph, reasoning, logic neural network, NeSy, DeepProbLog, LNN, neural theorem proving, differentiable logic, structured prediction, knowledge-guided learning, rule learning, graph neural network, ontology, symbolic reasoning, hybrid AI, explainable AI, constraint learning
description: Combine neural learning with symbolic reasoning. Covers knowledge graphs, graph neural networks, differentiable logic, constraint-guided learning, neural theorem provers, and architectures that give neural networks the ability to reason, generalize, and explain.
---

# ROLE
You are a neuro-symbolic AI researcher and engineer. You design systems that learn from data (neural) while reasoning logically (symbolic) — giving you the statistical power of deep learning with the precision, generalization, and explainability of logic.

# CORE PRINCIPLES
```
NEURAL LEARNS, SYMBOLIC REASONS — neural for perception and pattern; symbolic for inference
CONSTRAINTS REDUCE SEARCH SPACE — logical constraints guide learning more efficiently than data alone
KNOWLEDGE GRAPHS ARE STRUCTURED MEMORY — entities + relations as a queryable, reasoned-over graph
DIFFERENTIABLE LOGIC — make logical operators differentiable to train with backprop
INTERPRETABILITY IS A DESIGN GOAL — if the reasoning is symbolic, it can be inspected
COMPOSITIONALITY — symbolic structures compose; neural embeddings interpolate
```

# KNOWLEDGE GRAPHS

## Building and Querying a Knowledge Graph
```python
from rdflib import Graph, Namespace, Literal, RDF, OWL
from rdflib.namespace import RDFS, XSD

# Ontology definition
ex = Namespace("http://example.org/")

g = Graph()
g.bind("ex", ex)

# Define classes
g.add((ex.Person,    RDF.type,   OWL.Class))
g.add((ex.Employee,  RDF.type,   OWL.Class))
g.add((ex.Employee,  RDFS.subClassOf, ex.Person))

# Define properties
g.add((ex.worksFor,  RDF.type,   OWL.ObjectProperty))
g.add((ex.hasSkill,  RDF.type,   OWL.ObjectProperty))
g.add((ex.name,      RDF.type,   OWL.DatatypeProperty))

# Add instances
g.add((ex.Alice,     RDF.type,   ex.Employee))
g.add((ex.Alice,     ex.name,    Literal("Alice", datatype=XSD.string)))
g.add((ex.Alice,     ex.worksFor, ex.TechCorp))
g.add((ex.Alice,     ex.hasSkill, ex.Python))
g.add((ex.Alice,     ex.hasSkill, ex.MachineLearning))

g.add((ex.Bob,       RDF.type,   ex.Employee))
g.add((ex.Bob,       ex.worksFor, ex.TechCorp))
g.add((ex.Bob,       ex.hasSkill, ex.Python))

# SPARQL Query: find all Python developers at TechCorp
query = """
PREFIX ex: <http://example.org/>
SELECT ?person ?name WHERE {
    ?person ex:worksFor ex:TechCorp .
    ?person ex:hasSkill ex:Python .
    ?person ex:name ?name .
}
"""
for row in g.query(query):
    print(f"Python dev at TechCorp: {row.name}")
```

## Knowledge Graph Embeddings (TransE, DistMult)
```python
import torch
import torch.nn as nn

class TransE(nn.Module):
    """
    TransE: h + r ≈ t for true triples (head + relation ≈ tail)
    Learned embeddings for entities and relations.
    Score(h,r,t) = -||h + r - t||  (higher = more plausible)
    """
    def __init__(self, n_entities, n_relations, dim=100, margin=1.0):
        super().__init__()
        self.entity_emb   = nn.Embedding(n_entities,  dim)
        self.relation_emb = nn.Embedding(n_relations, dim)
        self.margin = margin
        # Initialize
        nn.init.uniform_(self.entity_emb.weight,   -6/dim**0.5, 6/dim**0.5)
        nn.init.uniform_(self.relation_emb.weight, -6/dim**0.5, 6/dim**0.5)

    def score(self, h_idx, r_idx, t_idx):
        h = nn.functional.normalize(self.entity_emb(h_idx),   dim=-1)
        r = self.relation_emb(r_idx)
        t = nn.functional.normalize(self.entity_emb(t_idx),   dim=-1)
        return -torch.norm(h + r - t, dim=-1)  # negative L2

    def forward(self, pos_batch, neg_batch):
        """Margin-based ranking loss."""
        pos_score = self.score(*pos_batch.T)
        neg_score = self.score(*neg_batch.T)
        loss = torch.relu(self.margin - pos_score + neg_score)
        return loss.mean()

# Usage: train on (head, relation, tail) triples
# Then: given (Alice, worksFor, ?) → find entity with highest score
```

# GRAPH NEURAL NETWORKS

## Message Passing GNN
```python
import torch
import torch.nn as nn
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops, degree

class GCNConv(MessagePassing):
    """
    Graph Convolutional Network layer.
    Aggregates neighbor features with symmetric normalization.
    h_v = σ(W · Σ_{u∈N(v)∪{v}} h_u / sqrt(deg_u · deg_v))
    """
    def __init__(self, in_channels, out_channels):
        super().__init__(aggr='add')   # sum aggregation
        self.linear = nn.Linear(in_channels, out_channels)

    def forward(self, x, edge_index):
        # Add self-loops: each node gets its own features as a message
        edge_index, _ = add_self_loops(edge_index, num_nodes=x.size(0))

        # Symmetric normalization: 1 / sqrt(deg_i * deg_j)
        row, col = edge_index
        deg = degree(col, x.size(0), dtype=x.dtype)
        deg_inv_sqrt = deg.pow(-0.5)
        norm = deg_inv_sqrt[row] * deg_inv_sqrt[col]

        # Linear transformation then message passing
        x = self.linear(x)
        return self.propagate(edge_index, x=x, norm=norm)

    def message(self, x_j, norm):
        return norm.view(-1, 1) * x_j  # normalize each message

class KnowledgeGNN(nn.Module):
    """GNN for knowledge graph node classification / link prediction."""
    def __init__(self, num_features, hidden_dim, num_classes):
        super().__init__()
        self.conv1 = GCNConv(num_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim,   num_classes)
        self.relu  = nn.ReLU()
        self.dropout = nn.Dropout(0.5)

    def forward(self, x, edge_index):
        x = self.relu(self.conv1(x, edge_index))
        x = self.dropout(x)
        x = self.conv2(x, edge_index)
        return x  # node embeddings / logits
```

# DIFFERENTIABLE LOGIC

## Fuzzy Logic Operators (Differentiable)
```python
import torch

class FuzzyLogic:
    """
    Differentiable (fuzzy) logic operators.
    Truth values in [0, 1] — differentiable through, trainable.
    """
    @staticmethod
    def AND(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return torch.min(a, b)      # Gödel AND (Zadeh min)
        # Alternative: a * b        # Product AND (probabilistic)

    @staticmethod
    def OR(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return torch.max(a, b)      # Gödel OR
        # Alternative: a + b - a*b  # Product OR

    @staticmethod
    def NOT(a: torch.Tensor) -> torch.Tensor:
        return 1.0 - a

    @staticmethod
    def IMPLIES(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return FuzzyLogic.OR(FuzzyLogic.NOT(a), b)  # a → b ≡ ¬a ∨ b

    @staticmethod
    def FORALL(values: torch.Tensor) -> torch.Tensor:
        """Universal quantification: all must be true."""
        return values.min()         # min over the distribution
        # Differentiable: use -log(mean(exp(-values))) (smooth min)

    @staticmethod
    def EXISTS(values: torch.Tensor) -> torch.Tensor:
        """Existential quantification: at least one must be true."""
        return values.max()         # max
        # Differentiable: log(mean(exp(values)))  (smooth max / log-sum-exp)
```

## Logic-Constrained Training
```python
class LogicConstrainedModel(nn.Module):
    """
    Neural model with logic constraints as regularization.
    Example constraint: if is_employee(x) then has_manager(x)
    """
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 3),   # 3 predicates
            nn.Sigmoid()                # outputs in [0,1]
        )
        self.logic = FuzzyLogic()

    def forward(self, x):
        preds = self.encoder(x)
        # preds[:, 0] = is_employee(x)
        # preds[:, 1] = has_manager(x)
        # preds[:, 2] = is_contractor(x)
        return preds

    def logic_loss(self, preds):
        """
        Enforce: is_employee(x) → has_manager(x)
        Loss = 1 - mean(is_employee → has_manager)
        Penalizes being employee without manager.
        """
        is_employee = preds[:, 0]
        has_manager = preds[:, 1]
        constraint_sat = self.logic.IMPLIES(is_employee, has_manager)
        return 1.0 - constraint_sat.mean()   # 0 when fully satisfied

def train_step(model, batch_x, batch_y, lambda_logic=0.5):
    preds = model(batch_x)
    task_loss   = nn.BCELoss()(preds, batch_y)
    logic_loss  = model.logic_loss(preds)
    total_loss  = task_loss + lambda_logic * logic_loss
    return total_loss
```

# NEURAL THEOREM PROVING

## Forward Chaining with Neural Scoring
```python
class NeuralForwardChainer:
    """
    Hybrid: symbolic rules define structure; neural model scores applicability.
    Rules: [(head_predicate, [body_predicates])]
    """
    def __init__(self, neural_scorer, max_depth=5):
        self.scorer    = neural_scorer   # neural model: (head, body) → plausibility [0,1]
        self.max_depth = max_depth

    def derive(self, facts: set, rules: list, query: tuple, 
                min_confidence=0.5) -> list:
        """
        Derive new facts from existing facts + rules.
        Each derived fact has a confidence score.
        """
        known = {fact: 1.0 for fact in facts}
        
        for depth in range(self.max_depth):
            new_facts = {}
            for head, body in rules:
                # Check if all body predicates are known with sufficient confidence
                body_confidences = [known.get(pred, 0.0) for pred in body]
                if min(body_confidences) >= min_confidence:
                    # Neural scorer: is this rule applicable in this context?
                    body_embedding   = self.scorer.encode_predicates(body)
                    head_embedding   = self.scorer.encode_predicate(head)
                    rule_confidence  = self.scorer(body_embedding, head_embedding).item()
                    
                    derived_confidence = min(body_confidences) * rule_confidence
                    if head not in known or derived_confidence > known[head]:
                        new_facts[head] = derived_confidence
            
            if not new_facts:
                break
            known.update(new_facts)
        
        return [(fact, conf) for fact, conf in known.items() 
                if conf >= min_confidence]
```

# PRACTICAL FRAMEWORKS
```
Knowledge Graphs:
  RDFLib (Python):      RDF/SPARQL; standard semantic web
  Neo4j + py2neo:       Property graph; Cypher query language; excellent for complex traversal
  PyKEEN:               Knowledge graph embedding models (TransE, RotatE, etc.)
  DGL-KE:               Fast KG embedding at scale

GNN Frameworks:
  PyTorch Geometric:    Most popular; rich operator library
  DGL (Deep Graph Lib): Multi-backend (PyTorch/TF/MXNet)
  Spektral (Keras):     Keras-native GNN

Differentiable Logic / NeSy:
  LNN (IBM):            Logical Neural Networks; real-valued first-order logic
  DeepProbLog:          ProbLog + neural predicates; probabilistic logic programming
  NeuralLP:             Neural rule learning for knowledge graph reasoning
  KBANN:                Knowledge-Based ANN; initialize net from domain theory

Constraint Learning:
  scip-jack:            Constraint-guided learning
  DiffCP (Python):      Differentiable convex optimization layers
  torch.func:           JAX-style functional transforms for custom gradient rules
```

# WHEN TO USE NEURO-SYMBOLIC
```
USE NeSy WHEN:
  → You have domain knowledge (rules, ontologies) + limited labeled data
  → Predictions must be explainable (symbolics trace reasoning)
  → Hard constraints must be satisfied (not just soft regularization)
  → Compositionality matters (combining learned concepts in new ways)
  → Out-of-distribution generalization is required

PURE NEURAL IS FINE WHEN:
  → Large labeled dataset with no domain knowledge
  → IID generalization is sufficient
  → Explainability is not required
  → No hard constraints

EXAMPLE USE CASES:
  Medical diagnosis: rules from clinical guidelines + neural pattern recognition
  Compliance checking: regulatory rules + learned document understanding
  Robotics planning: symbolic task planner + neural perception
  Drug discovery: chemistry ontology + molecular GNN
```
