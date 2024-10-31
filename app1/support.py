def improve_nltk(article_text):
    # Preprocessing
    article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
    article_text = re.sub(r'\s+', ' ', article_text)
    formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text)
    formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
    sentence_list = nltk.sent_tokenize(article_text)
    stopwords = nltk.corpus.stopwords.words('english')

    # Word frequency and scoring sentences
    word_frequencies = {}
    for word in nltk.word_tokenize(formatted_article_text):
        if word not in stopwords:
            word_frequencies[word] = word_frequencies.get(word, 0) + 1
    maximum_frequency = max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word] /= maximum_frequency

    sentence_scores = {}
    for sent in sentence_list:
        for word in nltk.word_tokenize(sent.lower()):
            if word in word_frequencies and len(sent.split()) < 30:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]
                
    summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)
    return ' '.join(summary_sentences)

def improve_t5(text):
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    # Load T5 model and tokenizer once when the module is imported
    model_name = "t5-small"
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    input_text = f"paraphrase: {text} </s>"
    inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    
    outputs = model.generate(
        inputs,
        max_length=100,
        num_return_sequences=1,
        num_beams=5,
        early_stopping=True
    )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)