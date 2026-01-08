import type { APIRoute } from "astro";

interface SubmitRequest {
  email?: string;
  featureRequest?: string;
  source?: string;
}

interface SubmitResponse {
  success: boolean;
  message: string;
  joinedWaitlist?: boolean;
  submittedFeature?: boolean;
}

export const POST: APIRoute = async ({ request, locals }) => {
  const db = locals.runtime.env.DB;

  // Parse request body
  let body: SubmitRequest;
  try {
    body = await request.json();
  } catch {
    return new Response(
      JSON.stringify({ success: false, message: "Invalid JSON body" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const { email, featureRequest, source } = body;

  // Validate: at least one field must be provided
  if (!email && !featureRequest) {
    return new Response(
      JSON.stringify({
        success: false,
        message: "Please provide an email or feature request",
      }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  // Validate email format if provided
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return new Response(
      JSON.stringify({
        success: false,
        message: "Please enter a valid email address",
      }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  // Get client IP from CF headers
  const ipAddress =
    request.headers.get("CF-Connecting-IP") ||
    request.headers.get("X-Forwarded-For")?.split(",")[0] ||
    null;

  const response: SubmitResponse = {
    success: true,
    message: "",
    joinedWaitlist: false,
    submittedFeature: false,
  };

  try {
    let waitlistEntryId: string | null = null;

    // If email provided, add to waitlist (or get existing entry)
    if (email) {
      const normalizedEmail = email.toLowerCase().trim();

      // Check if email already exists
      const existing = await db
        .prepare("SELECT id FROM waitlist_entry WHERE email = ?")
        .bind(normalizedEmail)
        .first<{ id: string }>();

      if (existing) {
        waitlistEntryId = existing.id;
      } else {
        const id = crypto.randomUUID();
        await db
          .prepare(
            `INSERT INTO waitlist_entry (id, email, source, ip_address)
             VALUES (?, ?, ?, ?)`
          )
          .bind(id, normalizedEmail, source || "landing", ipAddress)
          .run();
        waitlistEntryId = id;
        response.joinedWaitlist = true;
      }
    }

    // If feature request provided, insert it
    if (featureRequest && featureRequest.trim()) {
      const id = crypto.randomUUID();
      const normalizedEmail = email ? email.toLowerCase().trim() : null;

      await db
        .prepare(
          `INSERT INTO feature_request (id, waitlist_entry_id, email, content, source, ip_address)
           VALUES (?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          waitlistEntryId,
          normalizedEmail,
          featureRequest.trim(),
          source || "landing",
          ipAddress
        )
        .run();
      response.submittedFeature = true;
    }

    // Build response message
    if (response.joinedWaitlist && response.submittedFeature) {
      response.message =
        "Thanks! You're on the list and we've noted your feedback.";
    } else if (response.joinedWaitlist) {
      response.message = "Thanks for signing up! We'll be in touch.";
    } else if (response.submittedFeature) {
      response.message = "Thanks for your feedback!";
    } else if (email) {
      // Email was provided but already existed, and no feature request
      response.message = "You're already on the list!";
    }

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Database error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        message: "Something went wrong. Please try again.",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
};
