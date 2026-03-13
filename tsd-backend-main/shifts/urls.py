from django.urls import path
from .views import (
    ShiftsListCreateView,
    ShiftsRetrieveView,
    ShiftsUpdateView,

    ShiftTemplatesListCreateView,
    ShiftTemplatesRetrieveUpdateDestroyView,

    ShiftTypesListCreateView,
    ShiftTypesRetrieveUpdateDestroyView,

    ScheduleView,

    CalendarAnomalyTypesListCreateView,
    CalendarAnomalyTypesRetrieveUpdateDestroyView,

    CalendarAnomaliesListCreateView,
    CalendarAnomaliesRetrieveUpdateDestroyView,
    CalendarAnomaliesByMonthView, ShiftPatternsListCreateView, ShiftPatternsRetrieveUpdateDestroyView,
    CreateExchangeView, ApproveExchangeView, ExchangeDetailView, CancelExchangeView, ExchangeHistoryView,
)


urlpatterns = [
    path('shifts/<str:id>/', ShiftsUpdateView.as_view(), name='shifts-update'),
    path('shifts/<int:pk>/', ShiftsRetrieveView.as_view(), name='shifts-detail'),
    path('shifts/', ShiftsListCreateView.as_view(), name='shifts-list-create'),

    path('shifts-exchange/create/', CreateExchangeView.as_view(), name='create-exchange'),
    path('shifts-exchange/<int:pk>/', ExchangeDetailView.as_view(), name='exchange-detail'),
    path('shifts-exchange/<int:pk>/approve/', ApproveExchangeView.as_view(), name='approve-exchange'),
    path('shifts-exchange/<int:pk>/cancel/', CancelExchangeView.as_view(), name='cancel-exchange'),
    path('shifts-exchange/<int:pk>/history/', ExchangeHistoryView.as_view(), name='exchange-history'),

    path('shift-templates/', ShiftTemplatesListCreateView.as_view(), name='shift-templates-list-create'),
    path('shift-templates/<int:pk>/', ShiftTemplatesRetrieveUpdateDestroyView.as_view(), name='shift-templates-retrieve-update-destroy'),

    path('shift-types/', ShiftTypesListCreateView.as_view(), name='shift-types-list-create'),
    path('shift-types/<int:pk>/',ShiftTypesRetrieveUpdateDestroyView.as_view(), name='shift-types-retrieve-update-destroy'),

    path('calendar-anomaly-types/', CalendarAnomalyTypesListCreateView.as_view(), name='calendar-anomaly-types-list-create'),
    path('calendar-anomaly-types/<int:pk>/', CalendarAnomalyTypesRetrieveUpdateDestroyView.as_view(), name='calendar-anomaly-types-retrieve-update-destroy'),

    path('calendar-anomalies/', CalendarAnomaliesListCreateView.as_view(), name='calendar-anomalies-list-create'),
    path('calendar-anomalies/<int:pk>/', CalendarAnomaliesRetrieveUpdateDestroyView.as_view(), name='calendar-anomalies-retrieve-update-destroy'),
    path('calendar-anomalies/<int:year>/<int:month>/', CalendarAnomaliesByMonthView.as_view(), name='calendar-anomalies-by-month'),

    path('schedule/<int:year>/<int:month>/', ScheduleView.as_view(), name='schedule'),

    path('shift-patterns/', ShiftPatternsListCreateView.as_view(), name='shift-patterns-list-create'),
    path('shift-patterns/<int:pk>', ShiftPatternsRetrieveUpdateDestroyView.as_view(), name='shift-patterns-retrieve-update-destroy'),
]