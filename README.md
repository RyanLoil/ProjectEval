# ProjectEval: A Benchmark for Programming Agents Automated Evaluation on Project-Level Code Generation

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

🎉ProjectEval is accepted by ACL 2025 Findings.

🏆Leaderboard: [ProjectEval LeaderBoard](https://ryanloil.github.io/ProjectEval/)

📫Contact: [Kaiyuan Liu](mailto:1171000408@stu.hit.edu.cn)


## 👋Overview

- **ProjectEval** is a multi-level benchmark designed to evaluate LLMs and agents on *project-level code generation* through realistic user interactions. It integrates **natural language**, **structured checklists**, and **code skeletons** as 3 different level inputs to simulate diverse development scenarios and support explainable evaluations.

![ProjectEval Structure](./assets/structure.png)

- **ProjectEval** introduces automated evaluation tools and heterogeneous software verification systems, enabling fine-grained comparison of model outputs across semantically equivalent input formats. This provides deeper insight into a model’s understanding of end-to-end software development.

![ProjectEval Reasoning](./assets/reasoning.png)

- Our findings show that while proprietary models outperform, **open-source models still struggle** with complex, project-scale tasks. **ProjectEval** fills a critical gap as the first benchmark to support *realistic, interaction-based assessment* for practical software engineering.

![ProjectEval Generation](./assets/generation.png)

# 🚀Quickstart

## Evaluation

### Execution

If you trust your LLM that it won't do harm to your device, you can run the execution evaluation process by just using `python run_judge.py`

### Objective Indicators

## Reasoning

ProjectEval is an offline evaluation benchmark and its evalutaion phase is complicated and time-costy. So the reasoning phase is separated from the evaluation phase. 
The reasoning phase only produces JSON or files.

## Generation

# 🔍Citation

```
@misc{liu2025projectevalbenchmarkprogrammingagents,
      title={ProjectEval: A Benchmark for Programming Agents Automated Evaluation on Project-Level Code Generation}, 
      author={Kaiyuan Liu and Youcheng Pan and Jing Li and Daojing He and Yang Xiang and Yexing Du and Tianrun Gao},
      year={2025},
      eprint={2503.07010},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2503.07010}, 
}
```

# Known Issues

- [ ] There are a request making during execution evaluation. We are working on remove it.
