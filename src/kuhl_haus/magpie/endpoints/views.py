from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import transaction

from kuhl_haus.magpie.endpoints.models import EndpointModel, DnsResolver, DnsResolverList
from kuhl_haus.magpie.endpoints.forms import EndpointModelForm, DnsResolverForm, DnsResolverListForm


# EndpointModel Views
class EndpointListView(ListView):
    model = EndpointModel
    context_object_name = 'endpoints'
    template_name = 'endpoints/endpoint_list.html'


class EndpointDetailView(DetailView):
    model = EndpointModel
    context_object_name = 'endpoint'
    template_name = 'endpoints/endpoint_detail.html'


class EndpointCreateView(CreateView):
    model = EndpointModel
    form_class = EndpointModelForm
    template_name = 'endpoints/endpoint_form.html'
    success_url = reverse_lazy('endpoint-list')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save(commit=True)
            messages.success(self.request, "Endpoint created successfully!")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error saving endpoint: {str(e)}")
            return self.form_invalid(form)


class EndpointUpdateView(UpdateView):
    model = EndpointModel
    form_class = EndpointModelForm
    template_name = 'endpoints/endpoint_form.html'

    def get_success_url(self):
        return reverse_lazy('endpoint-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save(commit=True)
            messages.success(self.request, "Endpoint updated successfully!")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error updating endpoint: {str(e)}")
            return self.form_invalid(form)


class EndpointDeleteView(DeleteView):
    model = EndpointModel
    context_object_name = 'endpoint'
    template_name = 'endpoints/endpoint_confirm_delete.html'
    success_url = reverse_lazy('endpoint-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Endpoint deleted successfully!")
        return super().delete(request, *args, **kwargs)


# DnsResolver Views
class DnsResolverListView(ListView):
    model = DnsResolver
    context_object_name = 'resolvers'
    template_name = 'endpoints/resolver_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resolver_lists'] = DnsResolverList.objects.all()
        return context


class DnsResolverDetailView(DetailView):
    model = DnsResolver
    context_object_name = 'resolver'
    template_name = 'endpoints/resolver_detail.html'


class DnsResolverCreateView(CreateView):
    model = DnsResolver
    form_class = DnsResolverForm
    template_name = 'endpoints/resolver_form.html'
    success_url = reverse_lazy('resolver-list')

    def form_valid(self, form):
        messages.success(self.request, "DNS Resolver created successfully!")
        return super().form_valid(form)


class DnsResolverUpdateView(UpdateView):
    model = DnsResolver
    form_class = DnsResolverForm
    template_name = 'endpoints/resolver_form.html'

    def get_success_url(self):
        return reverse_lazy('resolver-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "DNS Resolver updated successfully!")
        return super().form_valid(form)


class DnsResolverDeleteView(DeleteView):
    model = DnsResolver
    context_object_name = 'resolver'
    template_name = 'endpoints/resolver_confirm_delete.html'
    success_url = reverse_lazy('resolver-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "DNS Resolver deleted successfully!")
        return super().delete(request, *args, **kwargs)


# DnsResolverList Views
class DnsResolverListListView(ListView):
    model = DnsResolverList
    context_object_name = 'resolver_lists'
    template_name = 'endpoints/resolver_list_list.html'


class DnsResolverListDetailView(DetailView):
    model = DnsResolverList
    context_object_name = 'resolver_list'
    template_name = 'endpoints/resolver_list_detail.html'


class DnsResolverListCreateView(CreateView):
    model = DnsResolverList
    form_class = DnsResolverListForm
    template_name = 'endpoints/resolver_list_form.html'
    success_url = reverse_lazy('resolver-list-list')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save(commit=True)
            messages.success(self.request, "DNS Resolver List created successfully!")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error creating DNS Resolver List: {str(e)}")
            return self.form_invalid(form)


class DnsResolverListUpdateView(UpdateView):
    model = DnsResolverList
    form_class = DnsResolverListForm
    template_name = 'endpoints/resolver_list_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.object:
            # Set initial data for the resolvers field
            form.fields['resolvers'].initial = [r.pk for r in self.object.resolvers.all()]
        return form

    def get_success_url(self):
        return reverse_lazy('resolver-list-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save(commit=True)
            messages.success(self.request, "DNS Resolver List updated successfully!")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error updating DNS Resolver List: {str(e)}")
            return self.form_invalid(form)


class DnsResolverListDeleteView(DeleteView):
    model = DnsResolverList
    context_object_name = 'resolver_list'
    template_name = 'endpoints/resolver_list_confirm_delete.html'
    success_url = reverse_lazy('resolver-list-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "DNS Resolver List deleted successfully!")
        return super().delete(request, *args, **kwargs)
