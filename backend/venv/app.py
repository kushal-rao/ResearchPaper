from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Mock data as fallback
MOCK_PAPERS = [
    {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        "summary": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        "link": "https://arxiv.org/abs/1706.03762",
        "published": "2017-06-12T17:18:52Z"
    },
    {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "summary": "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.",
        "link": "https://arxiv.org/abs/1512.03385",
        "published": "2015-12-10T18:40:12Z"
    },
    {
        "title": "Generative Adversarial Networks",
        "authors": ["Ian J. Goodfellow", "Jean Pouget-Abadie", "Mehdi Mirza"],
        "summary": "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D that estimates the probability that a sample came from the training data rather than G.",
        "link": "https://arxiv.org/abs/1406.2661",
        "published": "2014-06-10T19:55:15Z"
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        "summary": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
        "link": "https://arxiv.org/abs/1810.04805",
        "published": "2018-10-11T18:33:37Z"
    },
    {
        "title": "Mastering the Game of Go with Deep Neural Networks and Tree Search",
        "authors": ["David Silver", "Aja Huang", "Chris J. Maddison"],
        "summary": "The game of Go has long been viewed as the most challenging of classic games for artificial intelligence owing to its enormous search space and the difficulty of evaluating board positions and moves. Here we introduce a new approach to computer Go that uses 'value networks' to evaluate board positions and 'policy networks' to select moves.",
        "link": "https://arxiv.org/abs/1712.01815",
        "published": "2017-12-05T18:40:45Z"
    },
    {
        "title": "Language Models are Few-Shot Learners",
        "authors": ["Tom B. Brown", "Benjamin Mann", "Nick Ryder"],
        "summary": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task. While typically task-agnostic in architecture, this method still requires task-specific fine-tuning datasets of thousands or tens of thousands of examples.",
        "link": "https://arxiv.org/abs/2005.14165",
        "published": "2020-05-28T17:29:03Z"
    }
]

def fetch_arxiv_papers_simple(query="Computer Architecture", max_results=6):
    """Simple arXiv fetch with immediate fallback to mock data"""
    print(f"🔍 Searching for: {query}")
    
    try:
        # Simple arXiv API call
        base_url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        print(f"📡 Calling arXiv API...")
        response = requests.get(base_url, params=params, timeout=10)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ arXiv API failed with status {response.status_code}")
            return get_mock_papers_for_query(query, max_results)
        
        # Parse XML
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entries = root.findall('atom:entry', ns)
        print(f"📄 Found {len(entries)} entries from arXiv")
        
        if len(entries) == 0:
            print("⚠️  No entries found, using mock data")
            return get_mock_papers_for_query(query, max_results)
        
        papers = []
        for entry in entries:
            try:
                title = entry.find('atom:title', ns).text.strip()
                summary = entry.find('atom:summary', ns).text.strip()
                published = entry.find('atom:published', ns).text.strip()
                link = entry.find('atom:id', ns).text.strip()
                
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        authors.append(name.text.strip())
                
                papers.append({
                    'title': title,
                    'authors': authors if authors else ['Unknown Author'],
                    'summary': re.sub(r'\s+', ' ', summary),
                    'link': link,
                    'published': published
                })
                
            except Exception as e:
                print(f"⚠️  Error parsing entry: {e}")
                continue
        
        print(f"✅ Successfully parsed {len(papers)} papers from arXiv")
        return papers
        
    except Exception as e:
        print(f"❌ arXiv API error: {e}")
        print("🎭 Falling back to mock data")
        return get_mock_papers_for_query(query, max_results)

def get_mock_papers_for_query(query, max_results):
    """Get mock papers relevant to query"""
    print(f"🎭 Using mock data for query: {query}")
    
    # Filter mock papers based on query keywords
    query_words = query.lower().split()
    relevant_papers = []
    
    for paper in MOCK_PAPERS:
        paper_text = f"{paper['title']} {paper['summary']}".lower()
        if any(word in paper_text for word in query_words):
            relevant_papers.append(paper.copy())
    
    # If no relevant papers found, return some random papers
    if not relevant_papers:
        relevant_papers = MOCK_PAPERS[:max_results]
    
    # Add query-specific category
    for paper in relevant_papers:
        paper['category'] = query
    
    return relevant_papers[:max_results]

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Main search endpoint"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            query = data.get('query', 'machine learning')
            max_results = data.get('max_results', 6)
        else:
            query = request.args.get('query', 'machine learning')
            max_results = int(request.args.get('max_results', 6))
        
        print(f"\n🚀 New search request: '{query}' (max: {max_results})")
        
        papers = fetch_arxiv_papers_simple(query, max_results)
        
        response = {
            'success': True,
            'query': query,
            'count': len(papers),
            'papers': papers,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"📤 Returning {len(papers)} papers")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/papers', methods=['GET'])
def get_papers():
    """Legacy papers endpoint"""
    query = request.args.get('query', 'computer science')
    max_results = int(request.args.get('max_results', 6))
    
    papers = fetch_arxiv_papers_simple(query, max_results)
    return jsonify(papers)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'arXiv Research Dashboard API',
        'version': '3.0',
        'port': 8000,
        'endpoints': {
            '/search': 'GET/POST - Search papers',
            '/papers': 'GET - Legacy search',
            '/': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Research Dashboard API on port 8000...")
    print("📚 Will try arXiv API first, fallback to mock data if needed")
    print("🌐 CORS enabled for localhost:3000")
    print("💡 Test endpoint: http://127.0.0.1:8000/search?query=machine+learning")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8000)