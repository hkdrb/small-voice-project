
import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

// Force dynamic to prevent static optimization
export const dynamic = 'force-dynamic';
export const maxDuration = 300; // 5 minutes for Vercel/Next.js

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const cookieStore = await cookies();

    // Construct Cookie header string manually
    const allCookies = cookieStore.getAll()
      .map(c => `${c.name}=${c.value}`)
      .join('; ');

    // Determine Backend URL
    // In Docker, it is usually http://backend:8000
    // But locally might be localhost
    // We try to respect env or fallback to backend:8000 for Docker
    const backendUrl = process.env.INTERNAL_API_URL || 'http://backend:8000';
    const targetUrl = `${backendUrl}/api/dashboard/sessions/analyze`;

    console.log(`[Proxy] Forwarding analysis request to: ${targetUrl}`);

    // Create a controller for custom timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': allCookies, // Forward Auth
      },
      body: JSON.stringify(body),
      signal: controller.signal,
      cache: 'no-store'
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Proxy] Backend error: ${response.status} - ${errorText}`);
      return NextResponse.json(
        { error: `Backend failed: ${errorText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error: any) {
    console.error('[Proxy] Handler error:', error);
    if (error.name === 'AbortError') {
      return NextResponse.json({ error: 'Analysis timed out (5min limit)' }, { status: 504 });
    }
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
