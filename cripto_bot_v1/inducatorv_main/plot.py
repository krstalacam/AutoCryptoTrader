import plotly.graph_objs as go
from cripto_bot_v1.inducatorv_main.indicators.indicator_calculator import calculate_score_main

class Plotter:
    def __init__(self, crypto_symbol):
        self.crypto_symbol = crypto_symbol
        self.score_history = []

    def plot_data(self, data, trade_signals, total_profit_loss, trade_profit_loss):

        # Compute new score and update history
        new_score = calculate_score_main(data)
        if new_score is not None:
            self.score_history.append(new_score)

        # Prepare date range for score chart
        score_dates = data.index[:len(self.score_history)]

        # Calculate mean score
        mean_score = sum(self.score_history) / len(self.score_history) if self.score_history else 0

        # Main candlestick plot
        trace_price = go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name="Price",
            yaxis="y1"
        )

        # Moving averages
        trace_ema_longer = go.Scatter(
            x=data.index,
            y=data['sar'],
            mode='lines',
            name="sar",
            line=dict(color='orange', width=2),
            yaxis="y1"
        )
        trace_ema_long = go.Scatter(
            x=data.index,
            y=data['ema_long'],
            mode='lines',
            name="ema_long",
            line=dict(color='green', width=2),
            yaxis="y1"
        )
        trace_ema_short = go.Scatter(
            x=data.index,
            y=data['ema_short'],
            mode='lines',
            name="ema_short",
            line=dict(color='blue', width=2, dash='dot'),
            yaxis="y1"
        )

        # Buy and sell signals
        buy_signals = [
            go.Scatter(
                x=[signal['time']],
                y=[signal['price']],
                mode='markers',
                marker=dict(symbol='triangle-up', color='blue', size=10),
                name="Buy Signal",
                yaxis="y1"
            ) for signal in trade_signals if signal['type'] == 'buy'
        ]

        sell_signals = [
            go.Scatter(
                x=[signal['time']],
                y=[signal['price']],
                mode='markers',
                marker=dict(symbol='triangle-down', color='red', size=10),
                name="Sell Signal",
                yaxis="y1"
            ) for signal in trade_signals if signal['type'] == 'sell'
        ]

        # Score chart
        trace_score = go.Scatter(
            x=score_dates,
            #y=self.score_history,
            y=data['%K'],
            mode='lines+markers',
            name="Score",
            line=dict(color='pink', width=2, dash='dot'),
            yaxis="y3",
            hovertemplate='Score: %{y:.2f}<extra></extra>'
        )
        trace_score_v2 = go.Scatter(
            x=score_dates,
            # y=self.score_history,
            y=data['%D'],
            mode='lines+markers',
            name="Score",
            line=dict(color='purple', width=2, dash='dot'),
            yaxis="y3",
            hovertemplate='Score: %{y:.2f}<extra></extra>'
        )
        # Mean score line
        trace_mean_score = go.Scatter(
            x=score_dates,
            y=[mean_score] * len(score_dates),
            mode='lines',
            name="Mean Score",
            line=dict(color='red', width=2, dash='dash'),
            yaxis="y3"
        )

        # Create the layout with three y-axes
        layout = go.Layout(
            title=f"{self.crypto_symbol} Trading and Score Chart",
            height=1000,  # Maintained height
            showlegend=True,
            hovermode='x unified',
            xaxis=dict(title="Time"),
            yaxis=dict(title="Price", side='left', domain=[0.55, 1]),  # Slightly expanded price chart
            yaxis2=dict(title="", side='right', overlaying='y', showticklabels=False),
            yaxis3=dict(title="Score", side='right', domain=[0, 0.4])  # Maintained score chart domain
        )

        # Combine all traces
        fig = go.Figure(data=[
            trace_price, trace_ema_longer, trace_ema_long, trace_ema_short,
            *buy_signals, *sell_signals, trace_score,trace_score_v2, trace_mean_score
        ], layout=layout)

        # Profit annotations
        fig.add_annotation(
            x=0.5, y=1.15, text=f"Total Profit: {total_profit_loss:.2f}",
            showarrow=False, font=dict(size=14, color='green'), xref="paper", yref="paper"
        )
        fig.add_annotation(
            x=0.5, y=1.1, text=f"Trade P/L: {trade_profit_loss:.2f}",
            showarrow=False, font=dict(size=14, color='purple'), xref="paper", yref="paper"
        )

        return fig