TEST_CASES = {
        "valid": """
    print("Hello World")
    print(10 / 2)
    """,

        "zerodivision": """
    x = 10
    y = 0
    print(x / y)
    """,

        "indexerror": """
    numbers = [1, 2, 3]
    print(numbers[10])
    """,

        "keyerror": """
    student = {
        "name": "Josh",
        "age": 20
    }
    print(student["major"])
    """,

        "syntax": """
    def greet(name)
        print(f"Hello, {name}!")
    """
    }