"""Mock data layer.

Each module mirrors one of the documented sources (GSC, GA4, Semrush,
Semrush AI, and the CMSes) and exposes ``fetch(client, period)`` returning a
single period's data — exactly as a black-box API would. The report layer is
responsible for pulling two periods and computing the deltas.
"""
