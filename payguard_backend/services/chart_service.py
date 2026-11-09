# payguard_backend/services/chart_service.py
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for server rendering
import matplotlib.pyplot as plt
import io, base64

class ChartService:
    @staticmethod
    def generate_pillar_radar_chart(pillar_data):
        """
        Generates SITF Pillar Radar Chart using Matplotlib Agg backend.
        Returns base64 encoded PNG image for Django views.
        """
        categories = list(pillar_data.keys())
        values = list(pillar_data.values())
        
        fig, ax = plt.subplots(figsize=(6, 4), subplot_kw=dict(polar=True))
        # Render radar geometry
        ax.plot(categories, values, color='#d97706', linewidth=2)
        ax.fill(categories, values, color='#fbbf24', alpha=0.25)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')