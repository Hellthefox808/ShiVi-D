/// Briefing: Barrel file for all data models in the core/models directory.
/// Reason: A barrel file consolidates the exports of multiple files into a single module.
/// This allows other parts of the app to import all models using a single import statement 
/// (e.g., `import 'core/models/models.dart';`) rather than importing each file individually.

// Export the data model representing an incident report
export 'incident_model.dart';

// Export the data model representing a field task
export 'task_model.dart';

// Export the envelope model used for syncing data packets across the network
export 'event_envelope_model.dart';
