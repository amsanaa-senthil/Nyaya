import Sidebar from "@/components/dashboard/Sidebar";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen bg-[#0A1128]">
            <Sidebar />
            <main className="flex-1 flex flex-col h-screen overflow-hidden">
                {/* Header - could be another component */}
                <header className="h-16 border-b border-white/10 flex items-center justify-between px-8 bg-primary/50 backdrop-blur-md">
                    <h2 className="text-white font-semibold">User Dashboard</h2>
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-teal/20 border border-teal/50 flex items-center justify-center text-teal font-bold">
                            JD
                        </div>
                    </div>
                </header>

                {/* Dashboard Content */}
                <div className="flex-1 overflow-y-auto p-8 grid-pattern">
                    {children}
                </div>
            </main>
        </div>
    );
}
