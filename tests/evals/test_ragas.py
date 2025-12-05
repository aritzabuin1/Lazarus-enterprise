import pytest
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset
import os

# Skip if OPENAI_API_KEY is not set (e.g. in CI without secrets)
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API Key required for RAGAS")
def test_rag_evaluation():
    """
    Continuous Evaluation Pipeline using RAGAS.
    Goal: Ensure the RAG system provides relevant and faithful answers.
    """
    
    # 1. Golden Dataset (Ground Truth)
    # In a real scenario, load this from a JSON/CSV file.
    data = {
        'question': [
            'What is Lazarus Enterprise?', 
            'How does the pricing work?'
        ],
        'answer': [
            'Lazarus Enterprise is an AI automation platform for sales.', 
            'Pricing is based on usage and number of agents.'
        ],
        'contexts': [
            ['Lazarus Enterprise helps companies automate sales using AI agents.'], 
            ['Our pricing model scales with your needs, charging per active agent.']
        ],
        'ground_truth': [
            'Lazarus Enterprise is a platform for AI sales automation.', 
            'It costs money based on agents.'
        ]
    }
    
    dataset = Dataset.from_dict(data)
    
    # 2. Run Evaluation
    # Metrics:
    # - Faithfulness: Is the answer derived from the context? (Avoids hallucinations)
    # - Answer Relevancy: Does the answer address the question?
    results = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy]
    )
    
    # 3. Assert Quality Gates
    # If quality drops below 0.7, fail the build.
    print(f"RAGAS Results: {results}")
    
    assert results['faithfulness'] >= 0.7, "Faithfulness is too low!"
    assert results['answer_relevancy'] >= 0.7, "Answer is not relevant enough!"
