# cornell-admissions-faq-bot

How to use: go to [this link](https://cornell-faq-nyq3ekstz-vincent-fongs-projects.vercel.app/) and simply interact!

IMPORTANT NOTE: The model is reliant on [Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct), so the website may return an error for being overloaded from time to time. This should be temporary, interact with it at a different time.

How the model was created:
1. Scraped and preprocessed the data, isolating question/answer pairs present in the data.
2. Calculated embeddings of the question/answer pairs. 
3. Calculate most similar pairs to the query semantically based on embeddings.
4. Pass the pulled response(s) into my instruction-tuned LLM to polish the right answer.

The main design choice I made was choosing a threshold to determine what was a relevant answer worth parsing -- I chose 0.5 with decent results. 

Optional features included (and how I would expand upon this further):
1. Basic NLP techniques: semantics are considered already, but I would probably do some kind of keyword extraction on top of what I already have.
2. User feedback: currently the user can rate generated responses, we can probably improve on the log storage.