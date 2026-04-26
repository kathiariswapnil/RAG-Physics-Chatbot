from workflow import app

result = app.invoke({

    "question":
        "Derive the expression for escape velocity"

})

print(result["final_answer"])