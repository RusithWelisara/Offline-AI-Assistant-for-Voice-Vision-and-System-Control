# Offline AI Assistant for Voice, Vision, and System Control

---

This project is an offline-first AI assistant designed to operate without cloud dependency.
It integrates voice input, computer vision, decision logic, and hardware control into a single modular system.

The goal is not conversation — it is real-world task execution.

---

Most AI assistants rely heavily on cloud services, making them unsuitable for low-latency,
privacy-sensitive, or offline environments.

This project explores how far a fully local system can go while remaining usable, extensible,
and hardware-integrated.

---

## System Architecture

- Input Layer
  - Microphone (speech)
  - Camera (vision)
- Perception Layer
  - Speech-to-text
  - Object / gesture detection
- Reasoning Layer
  - Local language model
  - Intent routing
- Action Layer
  - OS automation
  - Hardware control (Arduino)
- Output Layer
  - Text-to-speech
  - Visual feedback

---

## Key Design Decisions

- Offline-first architecture to reduce latency and remove cloud dependency
- Modular pipeline to allow components (vision, voice, logic) to be swapped independently
- Clear separation between perception, reasoning, and action layers

---

## What This Project Demonstrates

- System-level thinking beyond single scripts
- Integration of AI with real hardware and operating systems
- Ability to design for constraints, not just features

---

## Status

The system is actively evolving as new capabilities are added and refined.
The focus remains on robustness, clarity, and real-world usability.

---

## Author
Rusith Welisara
AI systems builder focused on robotics and offline AI
