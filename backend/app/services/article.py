from typing import List, Optional


class ArticleService:
    articles = [
        {
            "id": 1,
            "title": "第一篇文章",
            "content": "这是第一篇文章的内容",
            "created_at": "2023-01-01",
            "author": "作者1"
        },
        {
            "id": 2,
            "title": "第二篇文章",
            "content": "这是第二篇文章的内容",
            "created_at": "2023-01-02",
            "author": "作者2"
        }
    ]

    @staticmethod
    def get_all():
        return ArticleService.articles

    @staticmethod
    def get_by_id(article_id: int):
        for article in ArticleService.articles:
            if article["id"] == article_id:
                return article
        return None
