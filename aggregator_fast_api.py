    import os
    import time
    import sqlite3
    import asyncio

    from dotenv import load_dotenv
    load_dotenv()
    API_KEY=os.getenv("API_KEY")

    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.messages import HumanMessage
    from langchain_core.messages import AIMessage

    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import Optional
    #fast_api_launcher = FastAPI(title="AI Aggregator API")
    app = FastAPI(title="AI Aggregator API")    


    class QuestionRequest(BaseModel):
        question: str
        model1: Optional[str] = "meta-llama/llama-3.3-70b-instruct:free"
        model2: Optional[str] = "google/gemma-3-27b-it:free"
        use_judge: Optional[bool] = True


    async def get_langchain_answer(model_name, user_text, chat_history=None):
        start_time = time.time()
        llm = ChatOpenAI(
            model = model_name,
            openai_api_key = API_KEY,
            base_url = "https://openrouter.ai/api/v1",
            max_tokens = 200
        )

        if chat_history is None:
            chat_history = []
        #prompt = ChatPromptTemplate("{topic}")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a useful assistant."),
            ("placeholder", "{chat_history}"),
            ("human", "{user_input}")
        ])
        chain = prompt | llm | StrOutputParser()

        result = await chain.ainvoke({
            "chat_history": chat_history or [],
            "user_input": user_text
        })

        duration = time.time() - start_time
        return result, duration



    async def judge_answers(user_text, answer1, answer2, model):
        if answer1[:100] == answer2[:100]:
            return answer1, 0.1
        start_time = time.time()
        llm = ChatOpenAI(
            model=model,
            openai_api_key=API_KEY,
            base_url="https://openrouter.ai/api/v1",
            max_tokens=500  
        )
        judge_template = """
        You are an expert who analyzes AI answers.

        Question: {question}

        ANSWER 1:
        {answer1}

        ANSWER 2:
        {answer2}

        Task:
        Using the two answers above, produce one single, high‑quality and concise final answer. Do not explain your reasoning, do not compare the answers, and do not mention which parts you selected. Simply provide the best possible final answer.

        FINAL ANSWER:
        """
        
        prompt = ChatPromptTemplate.from_template(judge_template)
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({
            "question": user_text,
            "answer1": answer1,
            "answer2": answer2
        })

        duration = time.time() - start_time
        return result, duration



    @app.post("/ask")
    async def ask_question(request: QuestionRequest):
        try:
            models = [
                "meta-llama/llama-3.3-70b-instruct:free",
                "google/gemma-3-27b-it:free"
            ]
            task1 = get_langchain_answer(models[0], request.question)
            task2 = get_langchain_answer(models[1], request.question)
            (answer1, duration1), (answer2, duration2) = await asyncio.gather(task1, task2)
            final_answer, judge_duration = await judge_answers(request.question, answer1, answer2, "mistralai/devstral-2512:free")

            conn = sqlite3.connect('my_aggregator.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO requests_history (question, model_name, answer, duration)
                VALUES (?, ?, ?, ?)
            ''', (request.question, models[0], answer1, duration1))

            cursor.execute('''
                INSERT INTO requests_history (question, model_name, answer, duration)
                VALUES (?, ?, ?, ?)
            ''', (request.question, models[1], answer2, duration2))
            
            cursor.execute('''
                INSERT INTO requests_history (question, model_name, answer, duration)
                VALUES (?, ?, ?, ?)
            ''', (request.question, "judge", final_answer, judge_duration))
            
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "question": request.question,
                "model1": {
                    "name": models[0],
                    "answer": answer1,
                    "duration": f"{duration1:.2f}s"
                },
                "model2": {
                    "name": models[1],
                    "answer": answer2,
                    "duration": f"{duration2:.2f}s"
                },
                "final_answer": final_answer,
                "total_duration": f"{duration1 + duration2 + judge_duration:.2f}s"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
        


    @app.get("/stats")
    def get_stats():
        conn = sqlite3.connect('my_aggregator.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                model_name,
                COUNT(*) as request_count,
                AVG(duration) as avg_duration,
                MIN(duration) as min_duration,
                MAX(duration) as max_duration
            FROM requests_history
            GROUP BY model_name
            ORDER BY request_count DESC
        ''')

        stats = cursor.fetchall()
        conn.close()
        result = []
        for row in stats:
            result.append({
                "model": row[0],
                "request_count": row[1],
                "avg_duration": f"{row[2]:.2f}s" if row[2] else "0.00s",
                "min_duration": f"{row[3]:.2f}s" if row[3] else "0.00s",
                "max_duration": f"{row[4]:.2f}s" if row[4] else "0.00s"
            })

        return {
            "statistics": result,
            "total_requests": sum(row[1] for row in stats) if stats else 0
        }



    @app.get("/history")
    def get_history(limit: int = 10):
        conn = sqlite3.connect('my_aggregator.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, question, model_name, duration
            FROM requests_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        history = cursor.fetchall()
        conn.close()

        return {
            "history": [
                {
                    "timestamp": row[0],
                    "question": row[1],
                    "model": row[2],
                    "duration": f"{row[3]:.2f}s" if row[3] else "0.00s"
                }
                for row in history
            ]
        }



    @app.delete("/clear")
    def clear_history():
        conn = sqlite3.connect('my_aggregator.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM requests_history')
        conn.commit()
        conn.close()
        
        return {"message": "History was cleared"}



    @app.get("/info")
    def get_info():
        return {
            "name": "AI Aggregator API",
            "version": "1.0",
            "available_models": [
                "meta-llama/llama-3.3-70b-instruct:free",
                "google/gemma-3-27b-it:free",
                "mistralai/devstral-2512:free (judge)"
            ],
            "features": [
                "Parallel queries to two models",
                "Automatic response validation",
                "Storage in SQLite database",
                "Detailed statistics"
            ]
        }



    def init_db():
        conn = sqlite3.connect('my_aggregator.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                question TEXT,
                model_name TEXT,
                answer TEXT,
                duration REAL
            )
        ''')
        conn.commit()
        conn.close()
        print("✅Datebase is ready to work")
    init_db()