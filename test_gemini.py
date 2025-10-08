from core import DataProcessor

if __name__ == "__main__":
    processor = DataProcessor()
    prompt = '{"message": "Say hello!"}'
    # Use a prompt that expects a JSON response
    result = processor.execute_ai_operation(
        'Respond ONLY with a JSON object: {"greeting": "Hello from Gemini!"}',
        operation_name="Test Greeting"
    )
    print("Gemini API test result:", result) 