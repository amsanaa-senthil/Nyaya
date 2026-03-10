"use client";

import React, { useState, useEffect } from 'react';
import { Quiz, Option } from '@/types/quiz';
import QuizCard from '@/components/quiz/QuizCard';
import QuestionCard from '@/components/quiz/QuestionCard';
import ProgressBar from '@/components/quiz/ProgressBar';
import ResultCard from '@/components/quiz/ResultCard';
import { ArrowLeft, ChevronRight, User } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';

// --- MOCK DATA ---
const mockQuizzes: Quiz[] = [
    {
        id: "q1",
        title: "Evolution of the Executive Presidency",
        description: "Traces how presidential powers expanded and were later restricted through major constitutional amendments.",
        difficulty: "Medium",
        durationMinutes: 12,
        questions: [
            {
                id: "q1_1",
                text: "The Executive Presidency in Sri Lanka was introduced under which Constitution?",
                options: [
                    { id: "o1", text: "Soulbury Constitution (1947)", isCorrect: false },
                    { id: "o2", text: "First Republican Constitution (1972)", isCorrect: false },
                    { id: "o3", text: "Second Republican Constitution (1978)", isCorrect: true },
                    { id: "o4", text: "19th Amendment (2015)", isCorrect: false }
                ],
                explanation: "The 1978 Constitution introduced the Executive Presidency, concentrating significant power in the hands of the President."
            },
            {
                id: "q1_2",
                text: "Which amendment significantly reduced the powers of the Executive Presidency?",
                options: [
                    { id: "o1", text: "13th Amendment", isCorrect: false },
                    { id: "o2", text: "18th Amendment", isCorrect: false },
                    { id: "o3", text: "19th Amendment", isCorrect: true },
                    { id: "o4", text: "20th Amendment", isCorrect: false }
                ],
                explanation: "The 19th Amendment (2015) curtailed presidential powers by restoring the two-term limit and establishing independent commissions."
            }
        ]
    },
    {
        id: "q2",
        title: "Fundamental Rights in Sri Lanka",
        description: "Test your knowledge on the fundamental rights guaranteed by the Constitution of Sri Lanka.",
        difficulty: "Easy",
        durationMinutes: 10,
        questions: [
            {
                id: "q2_1",
                text: "Under which chapter of the 1978 Constitution are Fundamental Rights enshrined?",
                options: [
                    { id: "o1", text: "Chapter I", isCorrect: false },
                    { id: "o2", text: "Chapter III", isCorrect: true },
                    { id: "o3", text: "Chapter VI", isCorrect: false },
                    { id: "o4", text: "Chapter X", isCorrect: false }
                ],
                explanation: "Chapter III of the 1978 Constitution specifically deals with Fundamental Rights."
            }
        ]
    },
    {
        id: "q3",
        title: "Land Law & Property Rights",
        description: "Complex scenarios involving land ownership, prescription, and partitioning in Sri Lanka.",
        difficulty: "Hard",
        durationMinutes: 20,
        questions: [
            {
                id: "q3_1",
                text: "In Sri Lanka, what is the statutory period for acquiring prescriptive title to private land?",
                options: [
                    { id: "o1", text: "5 years", isCorrect: false },
                    { id: "o2", text: "10 years", isCorrect: true },
                    { id: "o3", text: "15 years", isCorrect: false },
                    { id: "o4", text: "20 years", isCorrect: false }
                ],
                explanation: "Under the Prescription Ordinance, uninterrupted and adverse possession for 10 years is required to establish prescriptive title."
            }
        ]
    }
];

export default function QuizSystemPage() {
    const [quizzes, setQuizzes] = useState<Quiz[]>(mockQuizzes);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [activeQuizId, setActiveQuizId] = useState<string | null>(null);

    // State required by specifications
    const [currentQuestion, setCurrentQuestion] = useState<number>(0);
    const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
    const [score, setScore] = useState<number>(0);
    const [quizCompleted, setQuizCompleted] = useState<boolean>(false);

    // Extra state to track total correct/wrong
    const [correctCount, setCorrectCount] = useState<number>(0);
    const [wrongCount, setWrongCount] = useState<number>(0);

    // Example: How to fetch quizzes from your database
    /*
    useEffect(() => {
      const fetchQuizzesFromDB = async () => {
        try {
          setIsLoading(true);
          // Replace with your actual API endpoint (e.g., Supabase, MongoDB, Firebase via Next.js API route)
          const response = await fetch('/api/quizzes'); 
          if (response.ok) {
            const data = await response.json();
            setQuizzes(data);
          }
        } catch (error) {
          console.error("Failed to fetch quizzes, falling back to mock data", error);
        } finally {
          setIsLoading(false);
        }
      };
      
      fetchQuizzesFromDB();
    }, []);
    */

    const activeQuiz = quizzes.find(q => q.id === activeQuizId);
    const question = activeQuiz?.questions[currentQuestion];

    const handleStartQuiz = (quizId: string) => {
        setActiveQuizId(quizId);
        setCurrentQuestion(0);
        setSelectedAnswer(null);
        setScore(0);
        setCorrectCount(0);
        setWrongCount(0);
        setQuizCompleted(false);
    };

    const handleSelectOption = (optionId: string) => {
        if (selectedAnswer) return; // Prevent changing answer
        setSelectedAnswer(optionId);

        // Check correctness
        const option = question?.options.find(o => o.id === optionId);
        if (option?.isCorrect) {
            setScore(prev => prev + 1);
            setCorrectCount(prev => prev + 1);
        } else {
            setWrongCount(prev => prev + 1);
        }
    };

    const handleNextQuestion = () => {
        if (!activeQuiz) return;

        if (currentQuestion < activeQuiz.questions.length - 1) {
            setCurrentQuestion(prev => prev + 1);
            setSelectedAnswer(null);
        } else {
            setQuizCompleted(true);
        }
    };

    const resetQuiz = () => {
        if (activeQuizId) {
            handleStartQuiz(activeQuizId);
        }
    };

    const backToList = () => {
        setActiveQuizId(null);
        setQuizCompleted(false);
    };

    // View: Main List
    if (!activeQuizId || !activeQuiz) {
        return (
            <div className="min-h-screen bg-gray-50/20 p-6 md:p-12 pb-24 relative overflow-hidden font-sans">
                {/* Watermark Background */}
                <div className="absolute top-0 right-0 bottom-0 pointer-events-none z-0 opacity-[0.1] overflow-hidden flex justify-end items-end pb-12 pr-12 lg:pb-0 lg:pr-0 lg:items-center">
                    <img src="/logolaw.png" alt="Nyaya Background" className="h-[70vh] md:h-[90vh] lg:h-[120vh] max-w-none lg:translate-x-[15%] lg:translate-y-[20%] translate-x-[20%] translate-y-[15%] object-contain select-none grayscale" />
                </div>

                {/* Navbar */}
                <div className="w-full absolute top-0 left-0 right-0 z-20 flex items-center justify-between p-4 md:p-6 bg-gradient-to-b from-gray-50/80 to-transparent backdrop-blur-[2px]">
                    <div className="flex items-center gap-2.5">
                        <img src="/nyayalogo.png" alt="Nyaya Logo" className="h-8 md:h-10 w-auto" />
                        <span className="font-serif font-bold text-navy-900 text-lg md:text-xl tracking-tight">NYAYA.LK</span>
                    </div>
                    <button className="w-11 h-11 md:w-12 md:h-12 bg-navy-900 text-white rounded-full hover:bg-navy-800 transition shadow-sm flex items-center justify-center">
                        <User className="w-5 h-5 md:w-5 md:h-5 text-gold-500" />
                    </button>
                </div>

                <div className="max-w-6xl mx-auto relative z-10 pt-16 mt-8">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-12">
                        <div className="flex items-center gap-4">
                            <Link href="/" className="p-2 bg-white rounded-full hover:bg-gray-100 transition shadow-sm">
                                <ArrowLeft className="w-5 h-5 text-navy-900" />
                            </Link>
                            <h1 className="text-4xl font-serif font-bold text-navy-900">Revision Quizzes</h1>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {isLoading ? (
                            <div className="col-span-full py-12 flex justify-center text-navy-900/60 font-medium">
                                Loading quizzes from database...
                            </div>
                        ) : quizzes.length === 0 ? (
                            <div className="col-span-full py-12 flex justify-center text-navy-900/60 font-medium">
                                No quizzes found.
                            </div>
                        ) : (
                            <>
                                {quizzes.map(quiz => (
                                    <QuizCard key={quiz.id} quiz={quiz} onClick={handleStartQuiz} />
                                ))}
                                {/* Just showing extra copies so the grid looks full for demo purposes */}
                                {quizzes.map(quiz => (
                                    <QuizCard key={quiz.id + "_demo1"} quiz={{ ...quiz, id: quiz.id + "_demo1" }} onClick={handleStartQuiz} />
                                ))}
                            </>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    // View: Result View
    if (quizCompleted) {
        return (
            <div className="min-h-screen bg-gray-50/20 flex flex-col items-center justify-center p-6 pb-20 relative font-sans">
                {/* Navbar */}
                <div className="w-full absolute top-0 left-0 right-0 z-20 flex items-center justify-between p-4 md:p-6 bg-gradient-to-b from-gray-50/80 to-transparent backdrop-blur-[2px]">
                    <div className="flex items-center gap-2.5">
                        <img src="/nyayalogo.png" alt="Nyaya Logo" className="h-8 md:h-10 w-auto" />
                        <span className="font-serif font-bold text-navy-900 text-lg md:text-xl tracking-tight">NYAYA.LK</span>
                    </div>
                    <button className="w-11 h-11 md:w-12 md:h-12 bg-navy-900 text-white rounded-full hover:bg-navy-800 transition shadow-sm flex items-center justify-center">
                        <User className="w-5 h-5 md:w-5 md:h-5 text-gold-500" />
                    </button>
                </div>

                {/* Simple header for context inside quiz flow */}
                <div className="absolute top-24 md:top-28 left-8 z-10">
                    <button onClick={backToList} className="flex items-center text-sm font-medium text-navy-900/60 hover:text-navy-900 transition-colors">
                        <ArrowLeft className="w-4 h-4 mr-1" />
                        Back to Quizzes
                    </button>
                </div>

                <div className="mb-8 text-center">
                    <h2 className="text-2xl font-serif text-teal-700/80 tracking-wide">{activeQuiz.title}</h2>
                </div>

                <ResultCard
                    score={score}
                    totalQuestions={activeQuiz.questions.length}
                    correctCount={correctCount}
                    wrongCount={wrongCount}
                    onRetake={resetQuiz}
                    onBackToList={backToList}
                />
            </div>
        );
    }

    // View: Active Question View
    return (
        <div className="min-h-screen bg-gray-50/20 flex flex-col p-6 md:p-12 pb-24 relative overflow-hidden font-sans">
            {/* Watermark Background */}
            <div className="absolute top-0 right-0 bottom-0 pointer-events-none z-0 opacity-[0.1] overflow-hidden flex justify-end items-end pb-12 pr-12 lg:pb-0 lg:pr-0 lg:items-center">
                <img src="/logolaw.png" alt="Nyaya Background" className="h-[70vh] md:h-[90vh] lg:h-[120vh] max-w-none lg:translate-x-[15%] lg:translate-y-[20%] translate-x-[20%] translate-y-[15%] object-contain select-none grayscale" />
            </div>

            {/* Navbar */}
            <div className="w-full absolute top-0 left-0 right-0 z-20 flex items-center justify-between p-4 md:p-6 bg-gradient-to-b from-gray-50/80 to-transparent backdrop-blur-[2px]">
                <div className="flex items-center gap-2.5">
                    <img src="/nyayalogo.png" alt="Nyaya Logo" className="h-8 md:h-10 w-auto" />
                    <span className="font-serif font-bold text-navy-900 text-lg md:text-xl tracking-tight">NYAYA.LK</span>
                </div>
                <button className="w-11 h-11 md:w-12 md:h-12 bg-navy-900 text-white rounded-full hover:bg-navy-800 transition shadow-sm flex items-center justify-center">
                    <User className="w-5 h-5 md:w-5 md:h-5 text-gold-500" />
                </button>
            </div>

            <div className="w-full max-w-4xl mx-auto flex-1 flex flex-col relative z-10 pt-16 mt-4">
                <div className="flex items-center justify-between mb-8">
                    <button onClick={backToList} className="flex items-center px-4 py-2 bg-white rounded-full text-sm font-medium text-navy-900 hover:bg-gray-100 transition shadow-sm">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back
                    </button>
                    <div className="w-24 border border-transparent"></div> {/* Spacer for centering */}
                </div>

                {question && (
                    <div className="flex-1 flex flex-col justify-center">
                        <QuestionCard
                            quizTitle={activeQuiz.title}
                            questionNumber={currentQuestion + 1}
                            question={question}
                            selectedOptionId={selectedAnswer}
                            onSelectOption={handleSelectOption}
                        />
                    </div>
                )}

                {/* Progress & Navigation Footer */}
                <div className="mt-8 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-6 px-2">
                        <div className="w-1/3 text-left">
                            {/* Could house extra controls if needed */}
                        </div>
                        <div className="w-1/3 flex justify-center">
                            {/* Progress component handles its own text now, wait actually let's adjust */}
                        </div>
                        <div className="w-1/3 flex justify-end">
                            <button
                                onClick={handleNextQuestion}
                                disabled={!selectedAnswer}
                                className={`flex items-center px-8 py-3 rounded-xl font-medium transition-all ${selectedAnswer ? 'bg-navy-900 text-white hover:bg-navy-800 shadow-md' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                            >
                                {currentQuestion < activeQuiz.questions.length - 1 ? 'Next' : 'Finish'}
                                <ChevronRight className="w-4 h-4 ml-1" />
                            </button>
                        </div>
                    </div>
                    <ProgressBar current={selectedAnswer ? currentQuestion + 1 : currentQuestion} total={activeQuiz.questions.length} />
                </div>

            </div>
        </div>
    );
}
