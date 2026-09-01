---
title: "AI Concept Map"
type: "Index"
---

# AI Concept Map

A high-level Mermaid map connecting the major AI domains covered in this knowledge base.
For topic-level relationships, see each topic's "Related AI Topics" section.

```mermaid
flowchart TD
    AI[Artificial Intelligence Fundamentals]

    AI --> ML[Machine Learning]
    AI --> KR[Knowledge Representation]
    AI --> PLAN[AI Planning]
    AI --> UNC[Uncertainty in AI]

    ML --> ALGO[ML Algorithms]
    ML --> DL[Deep Learning]
    ML --> RL[Reinforcement Learning]

    DL --> CNN[Convolutional Neural Networks]
    DL --> RNN[Recurrent Neural Networks]
    DL --> TRANS[Transformer Architecture]
    DL --> GAN[Generative Adversarial Networks]

    TRANS --> LLM[Large Language Models]
    TRANS --> NLP[Natural Language Processing]

    NLP --> TC[Text Classification]
    NLP --> MT[Machine Translation]
    NLP --> QA[Question Answering]

    CNN --> CV[Computer Vision]
    CV --> OD[Object Detection]
    CV --> SEG[Image Segmentation]
    CV --> FR[Face Recognition]

    RNN --> SPEECH[Speech Recognition]
    SPEECH --> TTS[Text-to-Speech]
    SPEECH --> ASR[Automatic Speech Recognition]

    LLM --> GENAI[Generative AI]
    GENAI --> RAG[Retrieval-Augmented Generation]
    GENAI --> PROMPT[Prompt Engineering]
    GENAI --> DIFF[Diffusion Models]

    LLM --> AGENTS[AI Agents]
    AGENTS --> AGENTIC[Agentic AI]
    AGENTS --> TOOLS[Tool-Using AI]
    AGENTS --> MEM[Agent Memory]
    AGENTS --> MULTI[Multi-Agent Systems]

    ML --> ADV[Advanced AI Technologies]
    ADV --> KG[Knowledge Graphs]
    ADV --> VEC[Vector Embeddings]
    ADV --> XAI[Explainable AI]

    AI --> SAFETY[AI Safety Security and Ethics]
    SAFETY --> ALIGN[AI Alignment]
    SAFETY --> GOV[AI Governance]
    SAFETY --> BIAS[AI Bias and Fairness]

    ML --> INFRA[AI Infrastructure and Future]
    INFRA --> MLOPS[MLOps]
    INFRA --> EDGE[Edge AI]
    INFRA --> AGI[Artificial General Intelligence]
```

## Domain Summary

| Domain | Core Hub Topic | Feeds Into |
|--------|-----------------|------------|
| AI Fundamentals | [[Artificial Intelligence Fundamentals]] | Machine Learning, Planning, Reasoning |
| Machine Learning | [[Machine Learning]] | ML Algorithms, Deep Learning, RL |
| Deep Learning | [[Deep Learning]] | NLP, Computer Vision, Generative AI |
| NLP | [[Natural Language Processing]] | Large Language Models, Dialogue Systems |
| Computer Vision | [[Computer Vision]] | Object Detection, Segmentation, Video Understanding |
| Speech & Voice AI | [[Speech Recognition]] | Text-to-Speech, Audio Generation |
| Generative AI | [[Generative AI]] | RAG, Prompt Engineering, AI Agents |
| AI Agents | [[AI Agents]] | Agentic AI, Tool-Using AI, Multi-Agent Systems |
| Advanced AI | [[Knowledge Graphs]] | Vector Databases, Explainable AI |
| AI Safety | [[Responsible AI]] | Alignment, Governance, Fairness |
| Infrastructure | [[MLOps]] | LLMOps, Edge AI, TinyML |
