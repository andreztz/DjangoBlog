from django.contrib.syndication.views import Feed
from django.core import serializers
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_list_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from .models import Post
from .templatetags.markdownify import markdown


def home(request):
    if request.user.is_authenticated:
        posts = Post.objects.all()
    else:
        posts = Post.published.all()

    paginator = Paginator(posts, 5)
    page = request.GET.get("page")

    try:
        post_list = paginator.page(page)
    except PageNotAnInteger:
        post_list = paginator.page(1)
    except EmptyPage:
        post_list = paginator.paginator(paginator.num_pages)
    return render(request, "home.html", {"post_list": post_list})


def similar_posts_by_tag(request, tag_slug, pk):
    post = Post.objects.get(pk=pk)
    post_tags_ids = post.tags.values_list("id", flat=True)
    if request.user.is_authenticated:
        similar_posts = Post.objects.filter(tags__in=post_tags_ids).exclude(
            id=post.id
        )
        similar_posts = similar_posts.annotate(
            same_tags=Count("tags")
        ).order_by("-same_tags", "-publish")[:4]
    else:
        similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(
            id=post.id
        )
        similar_posts = similar_posts.annotate(
            same_tags=Count("tags")
        ).order_by("-same_tags", "-publish")[:4]
    return render(request, "tag.html", {"post_list": similar_posts})


def detail(request, slug):
    post = Post.objects.get(slug=slug)
    tags = post.tags.all()
    return render(request, "post.html", {"post": post, "tags": tags})


def about(request):
    return render(request, "about.html")


def archives(request):
    if request.user.is_authenticated:
        post_list = Post.objects.all()
    else:
        post_list = Post.published.all()
    return render(
        request, "archives.html", {"post_list": post_list, "error": False}
    )


def blog_search(request):
    if "search" in request.GET:
        search = request.GET["search"]
        if not search:
            return render(request, "home.html")
    else:
        post_list = get_list_or_404(
            Post.objects.filter(title__icontains=search)
        )
        if len(post_list) == 0:
            return render(
                request,
                "archives.html",
                {"post_list": post_list, "error": True},
            )
        else:
            return render(
                request,
                "archvies.html",
                {"post_list": post_list, "error": False},
            )
    return redirect("/")


class RSSFeed(Feed):
    title = "RSS feed - Articles"
    link = "/feeds/posts/"
    description = "RSS feed - Blog Posts"

    def items(self):
        return get_list_or_404(Post.published.all())

    def items_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.created_at

    def item_description(self, item):
        return markdown(item.content)
