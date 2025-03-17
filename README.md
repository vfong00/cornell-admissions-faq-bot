# cornell-admissions-faq-bot

How to use: go to [this link](cornell-faq-bot-git-main-vincent-fongs-projects.vercel.app) and simply interact!

IMPORTANT NOTE: The model is reliant on [Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct), so the website may return an error for being overloaded from time to time. This should be temporary, interact with it at a different time.

How the model was created:
1. Scraped and preprocessed the data, isolating question/answer pairs present in the data.
2. Calculated (and saved) embeddings of the question/answer pairs. 
3. Determined most relevant pairs to the query semantically with cosine similarity.
4. Pass the pulled response(s) into my instruction-tuned LLM to polish the right answer.


How I would expand upon this further:
- User feedback: currently the user can rate generated responses and the responses are saved to a simple SQLite database. It wouldn't be too hard to convert this to a cloud-based MySQL or PostgreSQL setup. This data can also be used to improve upon model answers.
- Response memory: The model does not remember its previous response or previous user queries. As such, there is no variety in how it responds.
- Model design: From an language processing perspective, I chose not to use keyword extraction because it didn't seem to give good results. I also wonder how the model would fare with a different confidence threshold.
