"use client";

import { motion } from "framer-motion";
import {
    History,
    MessageSquare,
    BookOpen,
    Trophy
} from "lucide-react";
import SpotlightCard from "@/components/SpotlightCard";

const OverviewPage = () => {
    const stats = [
        { label: "Chat Sessions", value: "12", icon: <MessageSquare className="text-teal" size={24} /> },
        { label: "Saved Citations", value: "48", icon: <BookOpen className="text-secondary" size={24} /> },
        { label: "Quizzes Completed", value: "8", icon: <Trophy className="text-teal-glow" size={24} /> },
        { label: "Study Hours", value: "24h", icon: <History className="text-white" size={24} /> },
    ];

    return (
        <div className="space-y-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
            >
                <h1 className="text-3xl font-serif font-bold text-white mb-2 text-left">Welcome back, John</h1>
                <p className="text-neutral-meta text-left">Your legal learning progress is looking great today.</p>
            </motion.div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, idx) => (
                    <SpotlightCard key={stat.label} delay={idx * 0.1} className="p-0">
                        <div className="flex flex-col items-center justify-center p-6 text-center">
                            <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-4">
                                {stat.icon}
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-1">{stat.value}</h3>
                            <p className="text-neutral-meta text-sm">{stat.label}</p>
                        </div>
                    </SpotlightCard>
                ))}
            </div>

            {/* Recent Activity */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="bg-primary-light/20 border border-white/10 rounded-2xl p-8"
            >
                <h2 className="text-xl font-bold text-white mb-6 text-left">Recent Activity</h2>
                <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer group">
                            <div className="w-10 h-10 rounded-lg bg-teal/10 flex items-center justify-center text-teal">
                                <MessageSquare size={18} />
                            </div>
                            <div className="flex-1 text-left">
                                <p className="text-white font-medium group-hover:text-teal-glow transition-colors">Legal Consultation on Rent Act</p>
                                <p className="text-neutral-meta text-xs">2 hours ago</p>
                            </div>
                            <div className="text-secondary text-xs font-bold uppercase tracking-wider">Completed</div>
                        </div>
                    ))}
                </div>
            </motion.div>
        </div>
    );
};

export default OverviewPage;
