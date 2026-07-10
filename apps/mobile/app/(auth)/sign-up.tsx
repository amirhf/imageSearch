import { Link, router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';

import { ActionButton } from '@/components/ActionButton';
import { Screen } from '@/components/Screen';
import { useSession } from '@/auth/useSession';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function SignUpScreen() {
  const { signUp, isConfigured } = useSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    setError(null);
    setMessage(null);
    setIsSubmitting(true);
    try {
      await signUp(email.trim(), password);
      setMessage('Account created. Check your email if confirmation is enabled.');
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen title="Create account" subtitle="Supabase auth keeps the mobile app aligned with web.">
      <View style={styles.panel}>
        {!isConfigured && (
          <Text style={styles.errorText}>
            Supabase env vars are missing. Add EXPO_PUBLIC_SUPABASE_URL and
            EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY.
          </Text>
        )}

        <TextInput
          autoCapitalize="none"
          autoComplete="email"
          autoCorrect={false}
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="Email"
          placeholderTextColor={colors.muted}
          style={styles.input}
          value={email}
        />
        <TextInput
          autoCapitalize="none"
          onChangeText={setPassword}
          placeholder="Password"
          placeholderTextColor={colors.muted}
          secureTextEntry
          style={styles.input}
          value={password}
        />

        {error && <Text style={styles.errorText}>{error}</Text>}
        {message && <Text style={styles.successText}>{message}</Text>}

        <ActionButton
          label={isSubmitting ? 'Creating...' : 'Create account'}
          onPress={handleSubmit}
          disabled={!isConfigured || isSubmitting || !email || !password}
        />

        <Link href="/sign-in" style={styles.link}>
          Already have an account?
        </Link>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  input: {
    backgroundColor: colors.canvas,
    borderColor: colors.border,
    borderRadius: radii.md,
    borderWidth: 1,
    color: colors.text,
    fontSize: 16,
    minHeight: 50,
    paddingHorizontal: spacing.md,
  },
  errorText: {
    color: colors.danger,
    fontSize: typography.caption,
    lineHeight: 18,
  },
  successText: {
    color: colors.success,
    fontSize: typography.caption,
    lineHeight: 18,
  },
  link: {
    color: colors.accent,
    fontSize: typography.body,
    fontWeight: '800',
    textAlign: 'center',
  },
});
