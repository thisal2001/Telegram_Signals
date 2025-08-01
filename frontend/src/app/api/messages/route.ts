import { NextResponse } from "next/server";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

export async function GET() {
  try {
    const signalQuery = `SELECT *, 'signal' AS message_type FROM signal_messages`;
    const marketQuery = `SELECT *, 'market' AS message_type FROM market_messages`;

    // Fetch from both tables
    const [signals, markets] = await Promise.all([
      pool.query(signalQuery),
      pool.query(marketQuery),
    ]);

    // Merge and sort by timestamp (descending)
    const messages = [...signals.rows, ...markets.rows].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    return NextResponse.json(messages);
  } catch (error) {
    console.error("❌ Error fetching historical messages:", error);
    return NextResponse.json({ error: "Failed to fetch messages" }, { status: 500 });
  }
}
