from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Now
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .constants import POSTS_LIMIT
from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

User = get_user_model()


def post_list_request(manager=Post.objects):
    return manager.select_related(
        'location', 'author', 'category'
    ).filter(
        pub_date__lte=Now(),
        is_published=True,
        category__is_published=True
    ).order_by(
        '-pub_date'
    )


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = POSTS_LIMIT
    profile = None

    def get_queryset(self):
        self.profile = get_object_or_404(User,
                                         username=self.kwargs['username'])

        if self.request.user == self.profile:
            return self.profile.post_set.select_related(
                'location', 'author', 'category'
            ).order_by(
                '-pub_date'
            )
        return post_list_request(self.profile.post_set)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ('username',
              'first_name',
              'last_name',
              'email',)

    def get_success_url(self) -> str:
        return reverse('blog:profile',
                       kwargs={'username': self.request.user})

    def get_object(self):
        return self.request.user


class IndexListView(ListView):
    queryset = post_list_request()
    ordering = '-pub_date'
    template_name = 'blog/index.html'
    paginate_by = POSTS_LIMIT


class PostDetailView(DetailView):
    model = Post
    template_name: str = 'blog/detail.html'
    pk_url_kwarg = 'post_pk'

    def get_object(self):
        obj = super().get_object()

        if ((obj.author != self.request.user)
            and (not obj.is_published
                 or not obj.category.is_published)):
            raise Http404('Страница не найдена')

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comment_set.select_related('author')
        )
        return context


class CategoryPostsListView(ListView):
    category_obj = None
    template_name = 'blog/category.html'
    paginate_by = POSTS_LIMIT

    def dispatch(self, request, *args, **kwargs):
        self.category_obj = get_object_or_404(
            Category,
            slug=kwargs['category_slug'],
            is_published=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return post_list_request(self.category_obj.post_set)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category_obj
        return context


class PostMixin:
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user})


class PostUpdateView(LoginRequiredMixin, PostMixin, UpdateView):
    pk_url_kwarg = 'post_pk'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['post_pk'])

        if instance.author != request.user:
            return redirect('blog:post_detail',
                            post_pk=kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('blog:post_detail',
                       kwargs={'post_pk': self.object.pk})


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    pk_url_kwarg = 'post_pk'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['post_pk'])

        if instance.author != request.user:
            return redirect('blog:post_detail',
                            post_pk=kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PostForm(instance=self.object)
        context['form'] = form
        return context

    def get_success_url(self) -> str:
        return reverse('blog:profile',
                       kwargs={'username': self.request.user})


class CommentBase():
    model = Comment
    template_name = 'blog/comment.html'
    post_: Post = None


class CommentCreateView(LoginRequiredMixin, CommentBase, CreateView):
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.post_ = get_object_or_404(Post, pk=kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', kwargs={'post_pk': self.post_.pk})


class CommentUpdateView(LoginRequiredMixin, CommentBase, UpdateView):
    form_class = CommentForm
    pk_url_kwarg = 'comment_pk'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_pk'])

        if instance.author != request.user:
            return redirect('blog:post_detail',
                            post_pk=kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('blog:post_detail',
                       kwargs={'post_pk': self.kwargs['post_pk']})


class CommentDeleteView(LoginRequiredMixin, CommentBase, DeleteView):
    pk_url_kwarg = 'comment_pk'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_pk'])

        if instance.author != request.user:
            return redirect('blog:post_detail',
                            post_pk=kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('blog:post_detail',
                       kwargs={'post_pk': self.kwargs['post_pk']})
