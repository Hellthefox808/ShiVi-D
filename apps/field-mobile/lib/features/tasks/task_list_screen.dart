import 'package:flutter/material.dart';
import '../../core/database/database.dart';

class TaskListScreen extends StatelessWidget {
  final List<LocalTaskEntity> tasks;
  final Function(String taskId, String nextStatus) onStatusChange;

  const TaskListScreen({
    Key? key,
    required this.tasks,
    required this.onStatusChange,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ShiVi Field Squad Tasks'),
        backgroundColor: const Color(0xFF0F172A),
      ),
      body: tasks.isEmpty
          ? const Center(
              child: Text(
                'No active tasks assigned.\nOffline operational node ready.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey, fontSize: 16),
              ),
            )
          : ListView.builder(
              itemCount: tasks.length,
              itemBuilder: (context, index) {
                final task = tasks[index];
                final isBlocked = task.isRouteBlocked == 'TRUE';

                return Card(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  color: isBlocked ? const Color(0xFF450A0A) : const Color(0xFF1E293B),
                  shape: RoundedRectangleBorder(
                    side: BorderSide(
                      color: isBlocked ? Colors.redAccent : Colors.blueGrey,
                      width: 1.5,
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (isBlocked) ...[
                          Row(
                            children: const [
                              Icon(Icons.warning_amber_rounded, color: Colors.redAccent, size: 20),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'SAFETY FREEZE: ROUTE CONTRADICTED',
                                  style: TextStyle(
                                    color: Colors.redAccent,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const Divider(color: Colors.redAccent, height: 16),
                        ],
                        Text(
                          task.title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          task.description,
                          style: const TextStyle(color: Colors.white70, fontSize: 14),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Chip(
                              label: Text(task.status),
                              backgroundColor: Colors.blueAccent.withOpacity(0.2),
                              labelStyle: const TextStyle(color: Colors.cyanAccent),
                            ),
                            if (!isBlocked && task.status == 'OFFERED')
                              ElevatedButton(
                                onPressed: () => onStatusChange(task.id, 'ACCEPTED'),
                                style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                                child: const Text('ACCEPT'),
                              ),
                            if (!isBlocked && task.status == 'ACCEPTED')
                              ElevatedButton(
                                onPressed: () => onStatusChange(task.id, 'EN_ROUTE'),
                                style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                                child: const Text('EN ROUTE'),
                              ),
                            if (!isBlocked && task.status == 'EN_ROUTE')
                              ElevatedButton(
                                onPressed: () => onStatusChange(task.id, 'ON_SITE'),
                                style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
                                child: const Text('ON SITE'),
                              ),
                            if (!isBlocked && task.status == 'ON_SITE')
                              ElevatedButton(
                                onPressed: () => onStatusChange(task.id, 'COMPLETED'),
                                style: ElevatedButton.styleFrom(backgroundColor: Colors.teal),
                                child: const Text('COMPLETE'),
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
