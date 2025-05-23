from controller import MaskerController
from llm import GPTTest

if __name__ == '__main__':
    tester = MaskerController(
                answer_path="data/project_eval_answer.json",
                model_class=GPTTest,
                llm="gpt-4o",
                output_path = "data/masked.json"
    )
    tester.run()