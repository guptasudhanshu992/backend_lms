-- Create courses table (PostgreSQL compatible)
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    instructor TEXT,
    duration TEXT,
    level TEXT,
    price NUMERIC(10, 2),
    category TEXT,
    image_url TEXT,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create blogs table (PostgreSQL compatible)
CREATE TABLE IF NOT EXISTS blogs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    author TEXT,
    category TEXT,
    image_url TEXT,
    published BOOLEAN DEFAULT FALSE,
    publish_at TIMESTAMP,
    tags TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample courses (using TRUE for boolean)
INSERT INTO courses (title, description, instructor, duration, level, price, category, published)
VALUES 
('Financial Statement Analysis', 'Master the art of reading and analyzing financial statements. Learn to interpret balance sheets, income statements, and cash flow statements.', 'Dr. Sarah Chen', '8 weeks', 'Beginner', 299.99, 'Finance', TRUE),
('Investment Banking Fundamentals', 'Comprehensive introduction to investment banking, including M&A, capital markets, and financial modeling.', 'Michael Roberts', '12 weeks', 'Intermediate', 499.99, 'Investment', TRUE),
('Technical Trading Strategies', 'Learn proven technical analysis techniques and develop profitable trading strategies for stocks and forex.', 'David Martinez', '6 weeks', 'Advanced', 399.99, 'Trading', TRUE),
('Corporate Finance Essentials', 'Essential concepts in corporate finance including capital budgeting, cost of capital, and capital structure.', 'Prof. Amanda Lee', '10 weeks', 'Intermediate', 349.99, 'Finance', TRUE),
('Risk Management in Finance', 'Comprehensive guide to identifying, measuring, and managing financial risks in modern organizations.', 'James Wilson', '8 weeks', 'Advanced', 449.99, 'Finance', TRUE),
('Portfolio Management', 'Build and manage diversified investment portfolios using modern portfolio theory and asset allocation strategies.', 'Emily Thompson', '10 weeks', 'Intermediate', 379.99, 'Investment', TRUE)
ON CONFLICT DO NOTHING;

-- Insert sample blog posts (using TRUE for boolean)
INSERT INTO blogs (title, excerpt, content, author, category, published)
VALUES 
('Understanding Market Volatility in 2025', 'Recent market fluctuations have left many investors wondering about the best strategies...', 'Market volatility in 2025 has been characterized by rapid changes driven by geopolitical tensions, technological disruptions, and shifting monetary policies. In this comprehensive analysis, we explore the key factors contributing to current market dynamics and provide actionable insights for investors navigating these turbulent times. Understanding volatility is crucial for making informed investment decisions and protecting your portfolio from unnecessary risks.', 'Sarah Chen', 'Market Analysis', TRUE),
('5 Essential Investment Tips for Beginners', 'Starting your investment journey can be overwhelming. Here are five fundamental tips...', 'Investing can seem daunting for beginners, but with the right approach, anyone can build wealth over time. Our five essential tips cover diversification, understanding your risk tolerance, the importance of starting early, regular portfolio reviews, and staying informed about market trends. Each tip is backed by decades of market research and proven investment principles that have helped countless investors achieve their financial goals.', 'Michael Roberts', 'Investment Tips', TRUE),
('The Rise of ESG Investing', 'Environmental, Social, and Governance factors are reshaping the investment landscape...', 'ESG investing has moved from a niche strategy to mainstream consideration for institutional and retail investors alike. This article examines the growth of ESG-focused funds, the performance metrics that matter, and how companies are adapting their business models to meet ESG criteria. We also discuss the challenges in ESG reporting and standardization, and what the future holds for sustainable investing practices.', 'Amanda Lee', 'Industry Insights', TRUE)
ON CONFLICT DO NOTHING;
