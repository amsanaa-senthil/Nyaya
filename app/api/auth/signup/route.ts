import { NextResponse } from 'next/server'; //Formated responses such as success and error 
import bcrypt from 'bcryptjs'; //Scrambeling user PW
import { Client } from 'pg'; //Connection the DB*

export async function POST(request: Request) {
    try {
        const { firstName, surname, username, email, password } = await request.json();

        // Setup connection to your nyaya_db
        const client = new Client({
            connectionString: process.env.DATABASE_URL,
        });
        await client.connect();

        // Hashing the password
        const saltRounds = 10;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // Insert user into PostgreSQL
        const query = `
            INSERT INTO users (first_name, surname, username, password_hash, email)
            VALUES ($1, $2, $3, $4, $5) 
            RETURNING user_id, username;
        `; //  VALUES ($1, $2, $3, $4, $5) -> adding placeholders to prevent SQL injection
        
        const values = [firstName, surname, username, hashedPassword, email];
        const res = await client.query(query, values);
        
        await client.end();

        return NextResponse.json({ 
            message: "User created successfully!", 
            user: res.rows[0] 
        }, { status: 201 });

    } catch (error: any) {
        // Handle unique constraint errors (e.g., username already exists)
        //23505 -> code for Unique violation in postgreSQL
        if (error.code === '23505') {
            return NextResponse.json({ error: "Username or Email already taken" }, { status: 400 });
        }
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}