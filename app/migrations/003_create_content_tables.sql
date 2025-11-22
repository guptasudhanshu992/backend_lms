-- Create courses table
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    instructor TEXT NOT NULL,
    duration TEXT NOT NULL,
    level TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    image_url TEXT,
    published INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create blogs table
CREATE TABLE IF NOT EXISTS blogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL,
    category TEXT NOT NULL,
    image_url TEXT,
    published INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample courses
INSERT INTO courses (title, description, instructor, duration, level, price, category, published)
VALUES 
('Financial Statement Analysis', 'Master the art of reading and analyzing financial statements. Learn to interpret balance sheets, income statements, and cash flow statements.', 'Dr. Sarah Chen', '8 weeks', 'Beginner', 299.99, 'Finance', 1),
('Investment Banking Fundamentals', 'Comprehensive introduction to investment banking, including M&A, capital markets, and financial modeling.', 'Michael Roberts', '12 weeks', 'Intermediate', 499.99, 'Investment', 1),
('Technical Trading Strategies', 'Learn proven technical analysis techniques and develop profitable trading strategies for stocks and forex.', 'David Martinez', '6 weeks', 'Advanced', 399.99, 'Trading', 1),
('Corporate Finance Essentials', 'Essential concepts in corporate finance including capital budgeting, cost of capital, and capital structure.', 'Prof. Amanda Lee', '10 weeks', 'Intermediate', 349.99, 'Finance', 1),
('Risk Management in Finance', 'Comprehensive guide to identifying, measuring, and managing financial risks in modern organizations.', 'James Wilson', '8 weeks', 'Advanced', 449.99, 'Finance', 1),
('Portfolio Management', 'Build and manage diversified investment portfolios using modern portfolio theory and asset allocation strategies.', 'Emily Thompson', '10 weeks', 'Intermediate', 379.99, 'Investment', 1);

-- Insert sample blog posts
INSERT INTO blogs (title, excerpt, content, author, category, published)
VALUES 
('Understanding Market Volatility in 2025', 'Recent market fluctuations have left many investors wondering about the best strategies...', 'Market volatility in 2025 has been characterized by rapid changes driven by geopolitical tensions, technological disruptions, and shifting monetary policies. In this comprehensive analysis, we explore the key factors contributing to current market dynamics and provide actionable insights for investors navigating these turbulent times. Understanding volatility is crucial for making informed investment decisions and protecting your portfolio from unnecessary risks.', 'Sarah Chen', 'Market Analysis', 1),
('5 Essential Investment Tips for Beginners', 'Starting your investment journey can be overwhelming. Here are five fundamental tips...', 'Investing can seem daunting for beginners, but with the right approach, anyone can build wealth over time. Our five essential tips cover diversification, understanding your risk tolerance, the importance of starting early, regular portfolio reviews, and staying informed about market trends. Each tip is backed by decades of market research and proven investment principles that have helped countless investors achieve their financial goals.', 'Michael Roberts', 'Investment Tips', 1),
('The Rise of ESG Investing', 'Environmental, Social, and Governance factors are reshaping the investment landscape...', 'ESG investing has moved from a niche strategy to mainstream consideration for institutional and retail investors alike. This article examines the growth of ESG-focused funds, the performance metrics that matter, and how companies are adapting their business models to meet ESG criteria. We also discuss the challenges in ESG reporting and standardization, and what the future holds for sustainable investing practices.', 'Amanda Lee', 'Industry Insights', 1);
