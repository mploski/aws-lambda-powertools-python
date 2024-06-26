from typing import Any, Dict, List

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncResolver()

posts_related = {
    "1": {"title": "post1"},
    "2": {"title": "post2"},
    "3": {"title": "post3"},
}


def search_batch_posts(posts: List) -> Dict[str, Any]:
    return {post_id: posts_related.get(post_id) for post_id in posts}


@app.batch_resolver(type_name="Query", field_name="relatedPosts")
def related_posts(event: List[AppSyncResolverEvent]) -> List[Any]:
    # Extract all post_ids in order
    post_ids = [record.arguments.get("post_id") for record in event]

    # Get unique post_ids while preserving order
    unique_post_ids = list(dict.fromkeys(post_ids))

    # Fetch posts in a single batch operation
    fetched_posts: Dict = search_batch_posts(unique_post_ids)

    # Return results in original order
    return [fetched_posts.get(post_id) for post_id in post_ids]


def lambda_handler(event, context: LambdaContext) -> dict:
    return app.resolve(event, context)
